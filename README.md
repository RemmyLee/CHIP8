![image](https://github.com/RemmyLee/CHIP8/assets/2806556/2e0d4e84-f9ec-45e2-a8fa-084edbbbd884)


# CHIP-8 Emulator

This Python project is an interpreter for the CHIP-8, an interpreted programming language developed in the mid-1970s. The emulator mimics the CHIP-8 environment, enabling the play of classic games designed for this platform.

## Features

- 4KB (4096 bytes) of memory
- 16 CPU registers
- Index and program counter
- Monochrome graphics system (64x32 pixels)
- Timers for delay and sound
- Input handling via a HEX-based keypad
- Fontset for display rendering

## Installation

Ensure you have Python installed on your system. You can then clone the project repository and navigate to its directory:

```bash
https://github.com/RemmyLee/CHIP8.git
cd CHIP8
```

### Dependencies

The emulator requires certain Python packages to function:

- `pygame` for sound and display
- `PyOpenGL` and `PyOpenGL_accelerate` for graphics

Install these with pip:

```bash
pip install pygame PyOpenGL PyOpenGL_accelerate
```

### Running a Game

To launch a CHIP-8 game with the emulator:

```bash
python3 main.py /path/to/rom
```

Replace `/path/to/rom` with the actual path to your CHIP-8 ROM.

## Controls

The original CHIP-8 keypad is mapped to the following keys on a standard keyboard:

| CHIP-8 Keypad | Keyboard Mapping |
|---------------|------------------|
| 1 2 3 C       | 1 2 3 4          |
| 4 5 6 D       | Q W E R          |
| 7 8 9 E       | A S D F          |
| A 0 B F       | Z X C V          |