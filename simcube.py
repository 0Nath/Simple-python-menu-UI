import pygame
import numpy as np
import math

class Cube:
    def __init__(self, screen, dimention):
        self.screen = screen
        self.dimentions = dimention
        self.end = False
        self.camera = [0, 2, 7]
        self.rotation_camera = [-0.35, 0, 0]
        self.surface = [160, 120, 300]

        self.cube = [
            [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
             (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)],
            [(0, 1), (1, 2), (2, 3), (3, 0),
             (4, 5), (5, 6), (6, 7), (7, 4),
             (0, 4), (1, 5), (2, 6), (3, 7)]
        ]


    def next_frame(self):
        self.render()
        pygame.display.flip()
        self.cube[0] = self.rotation_y(self.cube[0],0.01)


    def clear(self):
        self.screen.fill((0, 0, 0))

    def projection(self, a, c, o, e):

        rx = np.array([
            [1, 0, 0],
            [0, math.cos(o[0]), math.sin(o[0])],
            [0, -math.sin(o[0]), math.cos(o[0])]
        ])
        ry = np.array([
            [math.cos(o[1]), 0, -math.sin(o[1])],
            [0, 1, 0],
            [math.sin(o[1]), 0, math.cos(o[1])]
        ])
        rz = np.array([
            [math.cos(o[2]), math.sin(o[2]), 0],
            [-math.sin(o[2]), math.cos(o[2]), 0],
            [0, 0, 1]
        ])

        point = np.array([[a[0]], [a[1]], [a[2]]])
        cam = np.array([[c[0]], [c[1]], [c[2]]])
        transformed = rz @ ry @ rx @ (point - cam)

        if transformed[2][0] == 0:
            transformed[2][0] = 0.001  

        x = (e[2] / transformed[2][0]) * transformed[0][0] + e[0]
        y = (e[2] / transformed[2][0]) * transformed[1][0] + e[1]
        return (int(x), int(y))
    def rotation_y(self, points, angle):
        rot_y = np.array([
            [math.cos(angle), 0, math.sin(angle)],
            [0, 1, 0],
            [-math.sin(angle), 0, math.cos(angle)]
        ])
        rotated = []
        for p in points:
            v = np.array([[p[0]], [p[1]], [p[2]]])
            r = rot_y @ v
            rotated.append((r[0][0], r[1][0], r[2][0]))
        return rotated
    
    def draw_line(self, p1, p2):
        pygame.draw.line(self.screen, (255, 255, 255), p1, p2)

    def render(self):
        points = [self.projection(i, self.camera, self.rotation_camera, self.surface) for i in self.cube[0]]
        for i in self.cube[1]:
            self.draw_line(points[i[0]], points[i[1]])

