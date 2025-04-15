import pygame
import subprocess
import math
import os
import re
import psutil
import threading
import socket
import time
import simcube
from pygame.locals import *


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

        self.ANSI_REGEX = re.compile(r'\033\[(\d+)(;\d+)*m')
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

    

    def parse_ansi(self, text, initial_color):
        segments = []
        last_pos = 0
        current_color = initial_color
        
        i = 0
        while i < len(text):
            if text[i:i+2] == '\033[':
                if last_pos < i:
                    segments.append((text[last_pos:i], current_color))
                end = text.find('m', i)
                if end == -1:
                    break
                codes = text[i+2:end].split(';')
                for code in codes:
                    if code.isdigit():
                        code_num = int(code)
                        if code_num == 0:
                            current_color = self.font_color
                        elif code_num in self.ANSI_COLORS:
                            current_color = self.ANSI_COLORS[code_num]
                last_pos = end + 1
                i = last_pos
            else:
                i += 1

        if last_pos < len(text):
            segments.append((text[last_pos:], current_color))
            
        return segments, current_color

    def print_text(self, text: str, font_name: str, size: int, position: tuple, initial_color=None):
        font = pygame.font.SysFont(font_name, size)
        x, y = position
        if initial_color is None:
            initial_color = self.font_color

        segments, last_color = self.parse_ansi(text, initial_color)
        
        for segment, seg_color in segments:
            if not segment:
                continue
            clean_segment = re.sub(r'\033\[\d*[a-zA-Z]', '', segment)
            if clean_segment:
                surface = font.render(clean_segment, True, seg_color)
                self.screen.blit(surface, (x, y))
                x += surface.get_width()
        
        return last_color  # retourne la dernière couleur utilisée


    def event_handler(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                subprocess.run("DISPLAY=:0 xdotool key shift",shell=True)
                if event.key == pygame.K_UP:
                    self.menu.up()
                if event.key == pygame.K_DOWN:
                    self.menu.down()
                if event.key == pygame.K_LEFT:
                    self.menu.left()
                if event.key == pygame.K_RIGHT:
                    self.menu.right()

    def keyboard_event_handler(self):
        self.scroll_pos = 0
        self.end_loop = None
        while self.running:
            inpt = input()
            for i in inpt:
                if i == "u":
                    pygame.event.post(pygame.event.Event(KEYDOWN, key=K_UP))
                    self.scroll_pos+=4
                elif i == "d":
                    pygame.event.post(pygame.event.Event(KEYDOWN, key=K_DOWN))
                    self.scroll_pos-=4
                elif i == "l":
                    pygame.event.post(pygame.event.Event(KEYDOWN, key=K_LEFT))
                    self.end_loop = True
                elif i == "r":
                    pygame.event.post(pygame.event.Event(KEYDOWN, key=K_RIGHT))

    def render(self, menu):
        if menu.title.startswith("<DOn>"):
            self.end_loop = False
            func = globals().get(menu.title[5:])
            print(func)
            results = func().split("\n")
            pix_per_letter = math.floor((self.dimensions[0] / max([len(re.sub(r'\x1B\[[0-9;]*[a-zA-Z]', '', i)) for i in results])) / 0.6)
            self.scroll_pos = 0
            while not self.end_loop:
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        self.end_loop = True
                self.keys = pygame.key.get_pressed()
                if self.keys[pygame.K_LEFT]:
                    self.end_loop = True
                    self.menu.left()
                if self.keys[pygame.K_UP] and self.scroll_pos < 0:
                    self.scroll_pos += 2
                if self.keys[pygame.K_DOWN]:
                    self.scroll_pos -= 2

                self.screen.fill(self.bg_color)
                color = self.font_color
                for i, result in enumerate(results):
                    y = (pix_per_letter) * i + self.scroll_pos
                    color = self.print_text(result, self.font_name, pix_per_letter, (5, y), color)

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
        Case("<DOa>benchmark", []),
        Case("<DOa>updates", [])
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

def is_connected(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except OSError:
        return False
    

if os.name == 'nt':
    def neofetch():
        a =subprocess.run([
            "powershell", 
            "-Command", 
            "& 'C:\\Program Files\\WindowsPowerShell\\Scripts\\winfetch.ps1'"
        ], capture_output=True, text=True)
        return a.stdout
    Ui((320, 240), 60, menu)
    def ifconfig():
        return "Not aviable on Windows"
    def resource_monitor(screen,back_color,font_str,dim):
        return "Not aviable on Windows"


elif os.name == 'posix':
    os.environ['DISPLAY'] = ':0'
    def neofetch():
        # Don't strip ANSI escape sequences here
        a = subprocess.run("neofetch", capture_output=True, text=True, encoding="utf-8")
        # Remove specific ANSI sequences that control cursor position but keep color codes
        output = re.sub(r'\x1B\[[0-9;]*[ABCDEFGJKST]', '', a.stdout)
        return output
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
    def updates(screen, back_color, font_str, dim):
        font_size = 20
        font = pygame.font.SysFont(font_str, font_size)
        max_lines = dim[1] // (font_size + 5)

        process = subprocess.Popen(["sudo", "apt-get", "update", "-y"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True)

        lines = []
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                lines.append(output.strip())
                if len(lines) > max_lines:
                    lines.pop(0)  # garde que les dernières lignes

            screen.fill(back_color)
            for i, content in enumerate(lines):
                rendered = font.render(content, False, (255, 255, 255))
                screen.blit(rendered, (5, i * (font_size + 5)))
            pygame.display.flip()

        screen.fill(back_color)
        screen.blit(font.render("System will reboot now!", False, (255, 255, 255)), (5, 5))
        pygame.display.flip()
        time.sleep(2)
        subprocess.run("sudo reboot", shell=True)

    Ui((320, 240), 60, menu,font_name="Monospace",fullscreen=True)
