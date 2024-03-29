import pygame
import numpy as np


class Chip8Input:
    def __init__(self):
        self.key = np.zeros(16, dtype=np.uint8)  # 0-9, A-F
        self.key_map = {
            pygame.K_1: 0x1,
            pygame.K_2: 0x2,
            pygame.K_3: 0x3,
            pygame.K_4: 0xC,
            pygame.K_q: 0x4,
            pygame.K_w: 0x5,
            pygame.K_e: 0x6,
            pygame.K_r: 0xD,
            pygame.K_a: 0x7,
            pygame.K_s: 0x8,
            pygame.K_d: 0x9,
            pygame.K_f: 0xE,
            pygame.K_z: 0xA,
            pygame.K_x: 0x0,
            pygame.K_c: 0xB,
            pygame.K_v: 0xF,
        }
        self.reset_requested = False

    def set_keys(self):
        keys = pygame.key.get_pressed()
        for key, value in self.key_map.items():
            self.key[value] = 1 if keys[key] else 0
        if keys[pygame.K_0]:
            self.reset_requested = True

    def process_events(self, cpu):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if cpu.waiting_for_keypress:
                    for key, value in self.key_map.items():
                        if event.key == key:
                            cpu.V[cpu.key_register] = value
                            cpu.waiting_for_keypress = False
                            break
                if event.key in self.key_map:
                    self.key[self.key_map[event.key]] = 1
            elif event.type == pygame.KEYUP:
                if event.key in self.key_map:
                    self.key[self.key_map[event.key]] = 0
        return True
