import sys
import pygame
from cpu import Chip8CPU
from input import Chip8Input
from graphics import Chip8Graphics
from sound import Chip8Sound


def main(rom_file):
    # Initialize CPU, Input, Graphics, and Sound
    cpu = Chip8CPU()
    input_handler = Chip8Input()
    graphics = Chip8Graphics()
    sound = Chip8Sound()

    # Load the game
    cpu.load_game(rom_file)

    # Main emulation loop
    running = True
    while running:
        running = input_handler.process_events(cpu)
        cpu.emulate_cycle()
        input_handler.set_keys()
        cpu.keyboard = input_handler.key
        graphics.draw_graphics(cpu.display)
        sound.play_sound(cpu.sound_timer)
        pygame.display.flip()
        pygame.time.delay(2)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py [ROM file]")
        sys.exit(1)

    main(sys.argv[1])
