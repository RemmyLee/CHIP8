import pygame


class Chip8Sound:
    def __init__(self):
        pygame.mixer.init()
        self.beep_sound = pygame.mixer.Sound("beep.ogg")

    def play_sound(self, sound_timer):
        if sound_timer > 0:
            self.beep_sound.play()
