![image](https://github.com/RemmyLee/CHIP8/assets/2806556/2e0d4e84-f9ec-45e2-a8fa-084edbbbd884)


# CHIP-8 Emulator

A CHIP-8 interpreter wirtten in Python. The project uses the following structure:

main.py
- system/cpu.py
- system/input.py
- system/sound.py
- system/graphics.py

Included in the utils folder is a python script that can classify all the CHIP-8 roms in a directory and prepend them with the system type it's for.

- CHIP-8_PONG
- SUPERCHIP_octopeg.ch8
- XOCHIP_joust23.rom


## Features

- 4KB (4096 bytes) of memory
- 16 CPU registers
- Index and program counter
- Monochrome graphics system (64x32 pixels)
- Timers for delay and sound
- Input handling via a HEX-based keypad
- Fontset for display rendering

## Installation

```bash
https://github.com/RemmyLee/CHIP8.git
cd CHIP8
```

### Dependencies

Packages Needed:

- `pygame` for sound and display
- `PyOpenGL` and `PyOpenGL_accelerate` for graphics

Install these with pip:

```bash
pip install pygame PyOpenGL PyOpenGL_accelerate
```

### Running a Game

```bash
python3 main.py /path/to/rom
```

Replace `/path/to/rom` with the actual path to your CHIP-8 ROM.
Use "q+z" to reset.

## Controls

The original CHIP-8 keypad is mapped to the following keys on a standard keyboard:

| CHIP-8 Keypad | Keyboard Mapping |
|---------------|------------------|
| 1 2 3 C       | 1 2 3 4          |
| 4 5 6 D       | Q W E R          |
| 7 8 9 E       | A S D F          |
| A 0 B F       | Z X C V          |