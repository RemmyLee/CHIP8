import pygame
from OpenGL.GL import *
from OpenGL.GLUT import *


class Chip8Graphics:
    def __init__(self, width=640, height=320):
        self.window_width = width
        self.window_height = height
        pygame.init()
        pygame.display.set_mode(
            (self.window_width, self.window_height), pygame.DOUBLEBUF | pygame.OPENGL
        )
        glClearColor(0.44, 0.53, 0.0, 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, 64, 32, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        pygame.display.set_caption("CHIP-8 Emulator")

    def draw_graphics(self, display):
        glClear(GL_COLOR_BUFFER_BIT)
        glColor3f(0.25, 0.32, 0.11)
        scaling_factor = 1
        glBegin(GL_QUADS)
        for x in range(64):
            for y in range(32):
                if display[y][x] == 1:
                    glVertex2f(x * scaling_factor, y * scaling_factor)
                    glVertex2f((x + 1) * scaling_factor, y * scaling_factor)
                    glVertex2f((x + 1) * scaling_factor, (y + 1) * scaling_factor)
                    glVertex2f(x * scaling_factor, (y + 1) * scaling_factor)
        glEnd()
        pygame.display.flip()
