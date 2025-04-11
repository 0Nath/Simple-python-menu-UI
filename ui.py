import pygame
import subprocess
import math
import os
import re
import psutil
import threading
from pygame.locals import *
class Ui:
    def __init__(self, dim, fps, menu,color1=(48,48,48),color2=(35,35,35),back_color = (0,0,0),font_color=(255,255,255),font="consolas",font_size=25):
        self.dim = dim
        self.fps = fps
        self.font_str = font
        self.font_size = font_size
        self.font_color = font_color
        self.colors = [color1,color2]
        self.back_color = back_color
        pygame.init()
        self.screen = pygame.display.set_mode(self.dim)
        self.font = pygame.font.SysFont(self.font_str, self.font_size)
        self.clock = pygame.time.Clock()
        self.running = True
        self.menu = Menu(menu)
        threading.Thread(target=self.keyboard_event_handeler,daemon=True).start()
        while self.running:
            self.screen.fill(self.back_color)
            self.event_handeler()
            self.render(self.menu.get_menu())
            pygame.display.flip()
            self.clock.tick(self.fps)

    def event_handeler(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.menu.up()
                if event.key == pygame.K_DOWN:
                    self.menu.down()
                if event.key == pygame.K_LEFT:
                    self.menu.left()
                if event.key == pygame.K_RIGHT:
                    self.menu.right()
    def keyboard_event_handeler(self):
        while self.running:
            i = input()
            if i == "u":
                pygame.event.post(pygame.event.Event(KEYDOWN, key=K_UP))
            elif i == "d":
                pygame.event.post(pygame.event.Event(KEYDOWN, key=K_DOWN))
            elif i == "l":
                pygame.event.post(pygame.event.Event(KEYDOWN, key=K_LEFT))
            elif i == "r":
                pygame.event.post(pygame.event.Event(KEYDOWN, key=K_RIGHT))
    def render(self, menu):
        if menu.title.startswith("<DOn>"):
            end_loop = False
            fonction = globals().get(menu.title[5:])
            results = fonction()
            results = results.split("\n")
            pix_per_letter = math.floor((self.dim[0]/max([len(i) for i in results]))/0.6)
            
            temp_font = pygame.font.SysFont(self.font_str, pix_per_letter)
            scroll_pos = 0
            while not end_loop:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        end_loop = True
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_LEFT:
                            end_loop = True
                            self.menu.left()
                        if event.key == pygame.K_UP:
                            if scroll_pos<0:
                                scroll_pos+=5
                        if event.key == pygame.K_DOWN:
                                scroll_pos-=5
                            



                self.screen.fill(self.back_color)
                for i , result in enumerate(results):
                    text = temp_font.render(result, False, (255, 255, 255))
                    self.screen.blit(text, (5, (pix_per_letter)*i+scroll_pos))
                
                pygame.display.flip()
                self.clock.tick(self.fps)
        elif menu.title.startswith("<DOa>"):
            fonction = globals().get(menu.title[5:])
            fonction(self.screen,self.back_color,self.font_str,self.dim)
            self.menu.left()
        else:
            relative_offset = (self.font_size+20)*self.menu.curs_pos
            for j,i in enumerate(menu.submenu):
                if i.title[:5]=="<DOn>":
                    title = i.title[5:]
                else:
                    title = i.title
                text_color = (220, 220, 0) if j == self.menu.curs_pos else self.font_color
                self.render_box((j+1)*(self.font_size+20)-relative_offset, title, text_color)
            

            menu_points = [
                (0,0),(self.dim[0],0),
                (self.dim[0],0+self.font_size+20),(0,0+self.font_size+20)
            ]
            pygame.draw.polygon(self.screen,self.back_color,menu_points)
            title = menu.title+":"
            text = self.font.render(title, False, (255, 255, 255))
            self.screen.blit(text, (10, 10)) 
    def render_box(self,coord,content,color):
        box_points = [
            (0,coord),(self.dim[0],coord),
            (self.dim[0],coord+self.font_size+20),(0,coord+self.font_size+20)
        ]
        arrow_lines = [((self.dim[0]*0.8,coord+15),((self.dim[0]*0.8)+7,coord+(self.font_size+20)/2)),
                       ((self.dim[0]*0.8,coord+self.font_size+5),((self.dim[0]*0.8)+7,coord+(self.font_size+20)/2))]
        pygame.draw.polygon(self.screen,self.colors[0],box_points)
        pygame.draw.line(self.screen,self.colors[1],(0,coord),(self.dim[0],coord))
        pygame.draw.line(self.screen,self.colors[1],(0,coord+self.font_size+20),(self.dim[0],coord+self.font_size+20))
        pygame.draw.line(self.screen,color,arrow_lines[0][0],arrow_lines[0][1],2)
        pygame.draw.line(self.screen,color,arrow_lines[1][0],arrow_lines[1][1],2)
        text = self.font.render(content, False, color)
        self.screen.blit(text, (10, coord+10))
class Menu:
    def __init__(self, choices):
        self.menu = choices
        self.actualmenu = choices
        self.curs_pos = 0
        self.menu_pos = []

    def get_menu(self):
        return self.actualmenu

    def up(self):
        if self.curs_pos > 0:
            self.curs_pos -= 1

    def down(self):
        if self.curs_pos < len(self.actualmenu.submenu) - 1:
            self.curs_pos += 1

    def right(self):
        if self.curs_pos < len(self.actualmenu.submenu):
            self.menu_pos.append(self.curs_pos)
            self.curs_pos = 0
            self.goto(self.menu_pos)

    def left(self):
        if self.menu_pos:
            self.menu_pos.pop(-1)
            self.goto(self.menu_pos)

    def goto(self, pos):
        self.actualmenu = self.menu
        for i in pos:
            self.actualmenu = self.actualmenu.submenu[i]


class Case:
    def __init__(self, title, submenu):
        self.title = title
        self.submenu = submenu

# Structure du menu demandée
menu = Case("Tools", [
    Case("WiFi", [
        Case("Send", []),
        Case("Receive", [])
    ]),
    Case("Infrared", [
        Case("Send", []),
        Case("Receive", [])
    ]),
    Case("Info", [
        Case("<DOn>neofetch", []),
        Case("<DOn>ifconfig", []),
        Case("<DOa>resource_monitor", [])
    ])
])







if os.name == 'nt':
    def neofetch():
        a =subprocess.run([
            "powershell", 
            "-Command", 
            "& 'C:\\Program Files\\WindowsPowerShell\\Scripts\\winfetch.ps1'"
        ], capture_output=True, text=True)
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', a.stdout)
elif os.name == 'posix':
    def neofetch():
        a = subprocess.run("neofetch", capture_output=True, text=True, encoding="utf-8")
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', a.stdout)
    def ifconfig():
        a = subprocess.run("ip -4 addr show wlan0 | grep inet", capture_output=True,shell=True, text=True, encoding="utf-8").stdout.split(" ")
        b = ""
        for i in a:
            if i != "":
                b += i+"\n"
        return b
    


    def resource_monitor(screen,back_color,font_str,dim):
        end_loop = False
        while not end_loop:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    end_loop = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        end_loop = True

            cpu_per_core = psutil.cpu_percent(interval=0.5, percpu=True)
            memory = psutil.virtual_memory()
            results = ["CPU usage:"]
            for i, usage in enumerate(cpu_per_core):
                results.append(f"   core {i}: {usage}%")
            results.append(f"Memory:")
            results.append(f"   {math.floor(memory.used/1000000)}/{math.floor(memory.total/1000000)} Mbit  ")
            results.append(f"   {memory.percent}% used")
            line_space = (dim[0]/max([len(i) for i in results]))
            font = pygame.font.SysFont(font_str, math.floor(line_space/0.6))
            
            screen.fill(back_color)
            for i , result in enumerate(results):
                text = font.render(result, False, (255, 255, 255))
                screen.blit(text, (5, i*(line_space+10)))
            pygame.display.flip()
Ui((320, 240), 60, menu)
