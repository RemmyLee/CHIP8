import numpy as np
import pygame


class Chip8Sound:
    def __init__(self):
        pygame.mixer.init()
        self.beep_frequency = 400
        self.beep_duration = 0.2
        self.sample_rate = 44100
        self.beep_sound = self.generate_beep_sound()

    def generate_beep_sound(self):
        num_samples = int(self.sample_rate * self.beep_duration)
        t = np.arange(num_samples)

        # Generate a square wave
        wave = np.where(
            (t * self.beep_frequency // self.sample_rate) % 2 == 0, 32767, -32767
        )
        wave = (wave * 0.1).astype(np.int16)

        sound = pygame.mixer.Sound(buffer=wave.tobytes())
        sound.set_volume(0.1)
        return sound

    def play_sound(self, sound_timer):
        if sound_timer > 0:
            self.beep_sound.play()
