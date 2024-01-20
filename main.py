import contextlib

with contextlib.redirect_stdout(None):
    import pygame
import sys
from system.cpu import Chip8CPU
from system.input import Chip8Input
from system.graphics import Chip8Graphics
from system.sound import Chip8Sound


def main(rom_file):
    print("Welcome to CHIP-8 Emulator!")
    cpu = Chip8CPU()
    input_handler = Chip8Input()
    graphics = Chip8Graphics()
    sound = Chip8Sound()
    cpu.load_game(rom_file)
    running = True
    while running:
        cpu.emulate_cycle()
        running = input_handler.process_events(cpu)
        input_handler.set_keys()
        cpu.keyboard = input_handler.key
        graphics.draw_graphics(cpu.display)
        sound.play_sound(cpu.sound_timer)
        pygame.display.flip()
        pygame.time.delay(1)
        if input_handler.reset_requested:
            print("Reset requested")
            cpu.reset()
            cpu.load_game(rom_file)
            input_handler.reset_requested = False  # Reset the flag


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py [ROM file]")
        sys.exit(1)

    main(sys.argv[1])
