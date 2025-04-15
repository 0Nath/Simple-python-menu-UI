import pygame
import subprocess
import math
import os
import re
import psutil
import threading
from pygame.locals import *
import time
import simcube


class Ui:
    def __init__(self, dimensions: tuple, fps: int, menu: "Case",
                primary_color: tuple = (48, 48, 48), secondary_color: tuple = (35, 35, 35),
                bg_color: tuple = (0, 0, 0), font_color: tuple = (255, 255, 255),
                font_name: str = "consolas", font_size: int = 25, fullscreen: bool = False):
        self.dimensions = dimensions
        self.fps = fps
        self.font_name = font_name
        self.font_size = font_size
        self.font_color = font_color
        self.colors = [primary_color, secondary_color]
        self.bg_color = bg_color
        self.ANSI_COLORS = {
        30: (0, 0, 0),
        31: (255, 0, 0),
        32: (0, 255, 0),
        33: (255, 255, 0),
        34: (0, 0, 255),
        35: (255, 0, 255),
        36: (0, 255, 255),
        37: (255, 255, 255),
        90: (128, 128, 128),
        91: (255, 100, 100),
        92: (100, 255, 100),
        93: (255, 255, 100),
        94: (100, 100, 255),
        95: (255, 100, 255),
        96: (100, 255, 255),
        97: (255, 255, 255)
        }

        self.ANSI_REGEX = re.compile(r"\033\[(\d+)m")
        pygame.init()
        if not fullscreen:
            self.screen = pygame.display.set_mode(self.dimensions)
        else:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            pygame.mouse.set_visible(False)
        self.font = pygame.font.SysFont(self.font_name, self.font_size)
        self.clock = pygame.time.Clock()
        self.running = True
        self.menu = Menu(menu)
        threading.Thread(target=self.keyboard_event_handler, daemon=True).start()
        while self.running:
            self.screen.fill(self.bg_color)
            self.event_handler()
            self.render(self.menu.get_menu())
            pygame.display.flip()
            self.clock.tick(self.fps)

    

    def parse_ansi(self,text):
        segments = []
        last_pos = 0
        current_color = (255, 255, 255)
        for match in self.ANSI_REGEX.finditer(text):
            start, end = match.span()
            code = int(match.group(1))
            if start > last_pos:
                segments.append((text[last_pos:start], current_color))
            if code == 0:
                current_color = (255, 255, 255)  # reset
            elif code in self.ANSI_COLORS:
                current_color = self.ANSI_COLORS[code]
            last_pos = end
        if last_pos < len(text):
            segments.append((text[last_pos:], current_color))
        return segments

    def print_text(self, text: str, font_name: str, size: int, position: tuple):
        font = pygame.font.SysFont(font_name, size)
        x, y = position
        for segment, seg_color in self.parse_ansi(text):
            surface = font.render(segment, False, seg_color)
            self.screen.blit(surface, (x, y))
            x += surface.get_width()

    def event_handler(self):
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

    def keyboard_event_handler(self):
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
            func = globals().get(menu.title[5:])
            results = func().split("\n")
            pix_per_letter = math.floor((self.dimensions[0] / max([len(i) for i in results])) / 0.6)
            temp_font = pygame.font.SysFont(self.font_name, pix_per_letter)
            scroll_pos = 0
            while not end_loop:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        end_loop = True
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT]:
                    end_loop = True
                    self.menu.left()
                if keys[pygame.K_UP] and scroll_pos < 0:
                    scroll_pos += 2
                if keys[pygame.K_DOWN]:
                    scroll_pos -= 2
                self.screen.fill(self.bg_color)
                for i, result in enumerate(results):
                    self.print_text(result,self.font_name,pix_per_letter,(5, (pix_per_letter) * i + scroll_pos))
                pygame.display.flip()
                self.clock.tick(self.fps)


        elif menu.title.startswith("<DOa>"):
            func = globals().get(menu.title[5:])
            func(self.screen, self.bg_color, self.font_name, self.dimensions)
            self.menu.left()
        else:
            relative_offset = (self.font_size + 20) * self.menu.curs_pos
            for j, i in enumerate(menu.submenu):
                title = i.title[5:] if i.title[:5] in ["<DOn>", "<DOa>"] else i.title
                text_color = (220, 220, 0) if j == self.menu.curs_pos else self.font_color
                self.render_box((j + 1) * (self.font_size + 20) - relative_offset, title, text_color)

            menu_box = [
                (0, 0), (self.dimensions[0], 0),
                (self.dimensions[0], self.font_size + 20), (0, self.font_size + 20)
            ]
            pygame.draw.polygon(self.screen, self.bg_color, menu_box)
            title = menu.title + ":"
            text = self.font.render(title, False, (255, 255, 255))
            self.screen.blit(text, (10, 10))

    def render_box(self, coord, content, color):
        box_points = [
            (0, coord), (self.dimensions[0], coord),
            (self.dimensions[0], coord + self.font_size + 20), (0, coord + self.font_size + 20)
        ]
        arrow_lines = [
            ((self.dimensions[0] * 0.8, coord + 15), ((self.dimensions[0] * 0.8) + 7, coord + (self.font_size + 20) / 2)),
            ((self.dimensions[0] * 0.8, coord + self.font_size + 5), ((self.dimensions[0] * 0.8) + 7, coord + (self.font_size + 20) / 2))
        ]
        pygame.draw.polygon(self.screen, self.colors[0], box_points)
        pygame.draw.line(self.screen, self.colors[1], (0, coord), (self.dimensions[0], coord))
        pygame.draw.line(self.screen, self.colors[1], (0, coord + self.font_size + 20), (self.dimensions[0], coord + self.font_size + 20))
        pygame.draw.line(self.screen, color, arrow_lines[0][0], arrow_lines[0][1], 2)
        pygame.draw.line(self.screen, color, arrow_lines[1][0], arrow_lines[1][1], 2)
        text = self.font.render(content, False, color)
        self.screen.blit(text, (10, coord + 10))

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
    Case("Other", [
        Case("<DOn>neofetch", []),
        Case("<DOn>ifconfig", []),
        Case("<DOa>resource_monitor", []),
        Case("<DOa>benchmark", [])
    ])
])




def benchmark(screen,back_clolr,font_str,dimention):
    cube = simcube.Cube(screen,dimention)
    end = False
    font = pygame.font.SysFont(font_str,20)
    frames = 0
    last_time = time.time()
    text_fps = "-- FPS"
    while not end:
        cube.clear()

        frames += 1
        if time.time()-last_time>=1:
            last_time = time.time()
            text_fps = str(frames)+" FPS"
            frames = 0
        text = font.render(text_fps, False, (255,255,255))
        screen.blit(text, (10, 10))
        cube.next_frame()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                end = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    end = True
    cube = None
if os.name == 'nt':
    def neofetch():
        command = [
            "powershell", 
            "-ExecutionPolicy", "Bypass",
            "-Command", 
            "Invoke-Expression -Command \"& 'C:\\Program Files\\WindowsPowerShell\\Scripts\\winfetch.ps1'\""
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        return result.stdout
    Ui((320, 240), 60, menu)

elif os.name == 'posix':
    os.environ['DISPLAY'] = ':0'
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

            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
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
    def install_dependancy():
        subprocess.run("sudo apt install hcxdumptool",shell=True)

    #install_dependancy()

    Ui((320, 240), 60, menu,font="Monospace",fullscreen=True)
