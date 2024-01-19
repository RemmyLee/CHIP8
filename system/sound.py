import pygame
import os


class Chip8Sound:
    def __init__(self):
        pygame.mixer.init()
        current_script_path = os.path.dirname(__file__)
        beep_sound_path = os.path.join(current_script_path, "..", "BEEP", "beep.ogg")
        self.beep_sound = pygame.mixer.Sound(beep_sound_path)

    def play_sound(self, sound_timer):
        if sound_timer > 0:
            self.beep_sound.play()
