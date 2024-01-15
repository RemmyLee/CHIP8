# A CHIP8 Emulator written in Python

import time
import pygame
import logging
import os
import random
import sys

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Chip8:
    def __init__(self, filename):
        pygame.init()
        self.window_width, self.window_height = 640, 320
        self.display_surface = pygame.display.set_mode(
            (self.window_width, self.window_height)
        )
        pygame.display.set_caption("CHIP-8 Emulator")

        # Initialize CHIP-8 memory and registers
        self.memory = [0] * 4096  # 4KB of memory
        self.V = [0] * 16  # V registers
        self.I = 0  # Index register
        self.pc = 0x200  # Program counter starts at 0x200
        self.stack = [0] * 16  # Stack
        self.sp = -1  # Stack pointer, starts at -1 since it's used like a list index
        self.delay_timer = 0  # Delay timer
        self.sound_timer = 0  # Sound timer
        self.key = [0] * 16  # Keypad state
        self.display = [[0] * 64 for _ in range(32)]  # Display state
        self.waiting_for_keypress = False  # Is the emulator waiting for a keypress?
        self.key_register = None  # Which register should the keypress be stored in?
        self.opcode = 0  # Current opcode
        self.last_timer_update = time.time()  # Last time the timers were updated
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
        }  # Maps keys to their corresponding CHIP-8 key values
        self.opcode_table = {
            # Calls a more specific opcode function based on the first nibble.
            0x0000: self.opcode_0xxx,  # Calls RCA 1802 program at address NNN. Not necessary for most ROMs.
            0x1000: self.opcode_1xxx,  # Jumps to address NNN.
            0x2000: self.opcode_2xxx,  # Calls subroutine at NNN.
            0x3000: self.opcode_3xxx,  # Skips the next instruction if VX equals NN.
            0x4000: self.opcode_4xxx,  # Skips the next instruction if VX doesn't equal NN.
            0x5000: self.opcode_5xxx,  # Skips the next instruction if VX equals VY.
            0x6000: self.opcode_6xxx,  # Sets VX to NN.
            0x7000: self.opcode_7xxx,  # Adds NN to VX (carry flag is not changed).
            0x8000: self.opcode_8xxx,  # Calls a more specific opcode function based on the last nibble.
            0x9000: self.opcode_9xxx,  # Skips the next instruction if VX doesn't equal VY.
            0xA000: self.opcode_Axxx,  # Sets I to the address NNN.
            0xB000: self.opcode_Bxxx,  # Jumps to the address NNN plus V0.
            0xC000: self.opcode_Cxxx,  # Sets VX to the result of a bitwise AND operation on a random number and NN.
            0xD000: self.opcode_Dxxx,  # Draws a sprite at coordinate (VX, VY) with width of 8 pixels and height of N pixels.
            0xE000: self.opcode_Exxx,  # Calls a more specific opcode function based on the last two nibbles.
            0xF000: self.opcode_Fxxx,  # Calls a more specific opcode function based on the last two nibbles.
        }

        self.opcode_table_0xxx = {
            # Calls a more specific opcode function based on the last two nibbles.
            0x00E0: self.opcode_00E0,  # Clears the screen.
            0x00EE: self.opcode_00EE,  # Returns from a subroutine.
        }

        self.opcode_table_8xxx = {
            # Calls a more specific opcode function based on the last nibble.
            0x0000: self.opcode_8xy0,  # Sets VX to the value of VY. Performs a bitwise AND on the values of VX and VY, then stores the result in VX.
            0x0001: self.opcode_8xy1,  # Sets VX to VX OR VY. Performs a bitwise OR on the values of VX and VY, then stores the result in VX.
            0x0002: self.opcode_8xy2,  # Sets VX to VX AND VY. Performs a bitwise AND on the values of VX and VY, then stores the result in VX.
            0x0003: self.opcode_8xy3,  # Sets VX to VX XOR VY. Performs a bitwise exclusive OR on the values of VX and VY, then stores the result in VX.
            0x0004: self.opcode_8xy4,  # Adds VY to VX. VF is set to 1 when there's a carry, and to 0 when there isn't. Performs a bitwise addition on the values of VX and VY, then stores the result in VX.
            0x0005: self.opcode_8xy5,  # VY is subtracted from VX. VF is set to 0 when there's a borrow, and 1 when there isn't. Performs a bitwise subtraction on the values of VX and VY, then stores the result in VX.
            0x0006: self.opcode_8xy6,  # Shifts VX right by one. VF is set to the value of the least significant bit of VX before the shift. VX is divided by 2.
            0x0007: self.opcode_8xy7,  # Sets VX to VY minus VX. VF is set to 0 when there's a borrow, and 1 when there isn't. Sets VX to VY minus VX. VF is set to 0 when there's a borrow, and 1 when there isn't.
            0x000E: self.opcode_8xyE,  # Shifts VX left by one. VF is set to the value of the most significant bit of VX before the shift. VX is multiplied by 2.
        }

        self.opcode_table_Exxx = {
            # Calls a more specific opcode function based on the last two nibbles. Skips the next instruction if the key stored in VX is pressed.
            0x009E: self.opcode_Ex9E,  # Skips the next instruction if the key stored in VX is pressed. (Usually the next instruction is a jump to skip a code block)
            0x00A1: self.opcode_ExA1,  # Skips the next instruction if the key stored in VX isn't pressed. (Usually the next instruction is a jump to skip a code block)
        }

        self.opcode_table_Fxxx = {
            # Calls a more specific opcode function based on the last two nibbles. Sets VX to the value of the delay timer.
            0x0007: self.opcode_Fx07,  # Sets VX to the value of the delay timer. Sets VX to the value of the delay timer.
            0x000A: self.opcode_Fx0A,  # Waits for a key press and then stores it in VX. (Blocking Operation. All instruction halted until next key event)
            0x0015: self.opcode_Fx15,  # Sets the delay timer to VX. Sets the delay timer to VX.
            0x0018: self.opcode_Fx18,  # Sets the sound timer to VX. Sets the sound timer to VX.
            0x001E: self.opcode_Fx1E,  # Adds VX to I and sets VF to 1 if there's an overflow. Adds VX to I.
            0x0029: self.opcode_Fx29,  # Sets I to the location of the sprite for the character in VX. Characters 0-F (in hexadecimal) are represented by a 4x5 font.
            0x0033: self.opcode_Fx33,  # Stores the binary-coded decimal representation of VX at the addresses I, I+1, and I+2. Stores the binary-coded decimal representation of VX, with the most significant of three digits at the address in I, the middle digit at I plus 1, and the least significant digit at I plus 2.
            0x0055: self.opcode_Fx55,  # Stores V0 to VX in memory starting at address I. Copies the values of registers V0 through Vx into memory, starting at the address in I.
            0x0065: self.opcode_Fx65,  # Fills V0 to VX with values from memory starting at address I. Copies the values of memory addresses starting at the address in I into registers V0 through Vx.
        }
        self.load_fontset()  # Load the fontset into memory
        self.load_game(filename)

    def load_fontset(self):
        fontset = [
            0xF0,
            0x90,
            0x90,
            0x90,
            0xF0,  # 0
            0x20,
            0x60,
            0x20,
            0x20,
            0x70,  # 1
            0xF0,
            0x10,
            0xF0,
            0x80,
            0xF0,  # 2
            0xF0,
            0x10,
            0xF0,
            0x10,
            0xF0,  # 3
            0x90,
            0x90,
            0xF0,
            0x10,
            0x10,  # 4
            0xF0,
            0x80,
            0xF0,
            0x10,
            0xF0,  # 5
            0xF0,
            0x80,
            0xF0,
            0x90,
            0xF0,  # 6
            0xF0,
            0x10,
            0x20,
            0x40,
            0x40,  # 7
            0xF0,
            0x90,
            0xF0,
            0x90,
            0xF0,  # 8
            0xF0,
            0x90,
            0xF0,
            0x10,
            0xF0,  # 9
            0xF0,
            0x90,
            0xF0,
            0x90,
            0x90,  # A
            0xE0,
            0x90,
            0xE0,
            0x90,
            0xE0,  # B
            0xF0,
            0x80,
            0x80,
            0x80,
            0xF0,  # C
            0xE0,
            0x90,
            0x90,
            0x90,
            0xE0,  # D
            0xF0,
            0x80,
            0xF0,
            0x80,
            0xF0,  # E
            0xF0,
            0x80,
            0xF0,
            0x80,
            0x80,  # F
        ]
        for i in range(len(fontset)):
            self.memory[i] = fontset[i]  # Load the fontset into memory

    def fetch_opcode(self):
        """Fetches the next opcode from memory and increments the program counter."""
        print(f"Fetching opcode from address {hex(self.pc)}")
        self.opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]
        print(hex(self.opcode))

    def execute_opcode(self):
        """Calls a more specific opcode function based on the first nibble."""
        print(f"Executing opcode {hex(self.opcode)}")
        self.opcode_table[self.opcode & 0xF000]()

    def opcode_0xxx(self):
        """Calls a more specific opcode function based on the last two nibbles."""
        print(f"Calling opcode function {hex(self.opcode & 0x00FF)}")
        opcode = self.opcode & 0x00FF
        if opcode in self.opcode_table_0xxx:
            self.opcode_table_0xxx[opcode]()
            print(f"We hit the opcode {hex(opcode)}")
        else:
            logging.warning(
                f"Unknown opcode {hex(self.opcode)} encountered at address {hex(self.pc - 2)}"
            )

    def opcode_00E0(self):  # Clear the screen
        """Clears the screen."""
        print(f"Clearing the screen")
        self.display = [[0 for _ in range(64)] for _ in range(32)]
        self.pc += 2

    def opcode_00EE(self):  # Return from a subroutine
        """Return from a subroutine."""
        print(f"Returning from a subroutine")
        self.pc = self.stack[self.sp]  # Return to the stored address
        self.sp -= 1  # Decrement stack pointer
        self.pc += 2

    def opcode_1xxx(self):
        """Jumps to address NNN."""
        print(f"Jumping to address {hex(self.opcode & 0x0FFF)}")
        self.pc = self.opcode & 0x0FFF
        print(f"PC = {hex(self.pc)}")

    def opcode_2xxx(self):
        """Calls subroutine at NNN."""
        print(f"Calling subroutine at address {hex(self.opcode & 0x0FFF)}")
        self.sp += 1
        self.stack[
            self.sp
        ] = self.pc  # Store return address (next instruction after call)
        self.pc = self.opcode & 0x0FFF

    def opcode_3xxx(self):
        """Skips the next instruction if VX equals NN.
        The interpreter compares register VX to NN, and if they are equal, increments the program counter by 2.
        """
        print(f"Comparing V{self.opcode & 0x0F00 >> 8} to {hex(self.opcode & 0x00FF)}")
        if self.V[(self.opcode & 0x0F00) >> 8] == (self.opcode & 0x00FF):
            print(f"Opcode = {hex(self.opcode)}")
            self.pc += 2
        self.pc += 2

    def opcode_4xxx(self):
        """Skips the next instruction if VX doesn't equal NN."""
        print(f"Comparing V{self.opcode & 0x0F00 >> 8} to {hex(self.opcode & 0x00FF)}")
        if self.V[self.opcode & 0x0F00 >> 8] != (self.opcode & 0x00FF):
            self.pc += 2
        self.pc += 2

    def opcode_5xxx(self):
        """Skips the next instruction if VX equals VY."""
        print(f"Comparing V{self.opcode & 0x0F00 >> 8} to V{self.opcode & 0x00F0 >> 4}")
        if self.V[self.opcode & 0x0F00 >> 8] == self.V[self.opcode & 0x00F0 >> 4]:
            self.pc += 2
        self.pc += 2

    def opcode_6xxx(self):
        """Sets VX to NN."""
        print(f"Setting V{self.opcode & 0x0F00 >> 8} to {hex(self.opcode & 0x00FF)}")
        self.V[self.opcode & 0x0F00 >> 8] = self.opcode & 0x00FF
        self.pc += 2

    def opcode_7xxx(self):
        """Adds NN to VX (carry flag is not changed)."""
        print(f"Adding {hex(self.opcode & 0x00FF)} to V{self.opcode & 0x0F00 >> 8}")
        self.V[self.opcode & 0x0F00 >> 8] += self.opcode & 0x00FF
        self.pc += 2

    def opcode_8xxx(self):
        """Calls a more specific opcode function based on the last nibble."""
        print(f"Calling opcode function 8xxx")
        self.opcode_table_8xxx[self.opcode & 0x000F]()

    def opcode_8xy0(self):
        """Sets VX to the value of VY."""
        print(f"Setting V{self.opcode & 0x0F00 >> 8} to V{self.opcode & 0x00F0 >> 4}")
        self.V[self.opcode & 0x0F00 >> 8] = self.V[self.opcode & 0x00F0 >> 4]
        self.pc += 2

    def opcode_8xy1(self):
        """Sets VX to VX OR VY."""
        print(f"Setting V{self.opcode & 0x0F00 >> 8} to V{self.opcode & 0x00F0 >> 4}")
        self.V[self.opcode & 0x0F00 >> 8] |= self.V[self.opcode & 0x00F0 >> 4]
        self.pc += 2

    def opcode_8xy2(self):
        """Sets VX to VX AND VY."""
        print(f"Setting V{self.opcode & 0x0F00 >> 8} to V{self.opcode & 0x00F0 >> 4}")
        self.V[self.opcode & 0x0F00 >> 8] &= self.V[self.opcode & 0x00F0 >> 4]
        self.pc += 2

    def opcode_8xy3(self):
        """Sets VX to VX XOR VY."""
        print(f"Setting V{self.opcode & 0x0F00 >> 8} to V{self.opcode & 0x00F0 >> 4}")
        self.V[self.opcode & 0x0F00 >> 8] ^= self.V[self.opcode & 0x00F0 >> 4]
        self.pc += 2

    def opcode_8xy4(self):
        """Sets VX to VX + VY. VF is set to 1 when there's a carry, and to 0 when there isn't."""
        print(f"Adding V{self.opcode & 0x00F0 >> 4} to V{self.opcode & 0x0F00 >> 8}")
        self.V[self.opcode & 0x0F00 >> 8] += self.V[self.opcode & 0x00F0 >> 4]
        if self.V[self.opcode & 0x0F00 >> 8] > 0xFF:
            self.V[0xF] = 1
        else:
            self.V[0xF] = 0
        self.V[self.opcode & 0x0F00 >> 8] &= 0xFF
        self.pc += 2

    def opcode_8xy5(self):
        """Sets VX to VX - VY, set VF = NOT borrow."""
        print(
            f"Subtracting V{self.opcode & 0x00F0 >> 4} from V{self.opcode & 0x0F00 >> 8}"
        )
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        if self.V[x] >= self.V[y]:
            self.V[0xF] = 1
        else:
            self.V[0xF] = 0
        self.V[x] -= self.V[y]
        self.V[x] &= 0xFF  # Ensure Vx stays 8-bit
        self.pc += 2

    def opcode_8xy6(self):
        """Shifts VX right by one. VF is set to the value of the least significant bit of VX before the shift."""
        print(f"Shifting V{self.opcode & 0x0F00 >> 8} right by one")
        self.V[0xF] = self.V[self.opcode & 0x0F00 >> 8] & 0x1
        self.V[self.opcode & 0x0F00 >> 8] >>= 1
        self.pc += 2

    def opcode_8xy7(self):
        """Sets VX to VY - VX. VF is set to 0 when there's a borrow, and 1 when there isn't."""
        print(
            f"Subtracting V{self.opcode & 0x0F00 >> 8} from V{self.opcode & 0x00F0 >> 4}"
        )
        if self.V[self.opcode & 0x00F0 >> 4] > self.V[self.opcode & 0x0F00 >> 8]:
            self.V[0xF] = 1
        else:
            self.V[0xF] = 0
        self.V[self.opcode & 0x0F00 >> 8] = (
            self.V[self.opcode & 0x00F0 >> 4] - self.V[self.opcode & 0x0F00 >> 8]
        )
        self.pc += 2

    def opcode_8xyE(self):
        """Shifts VX left by one. VF is set to the value of the most significant bit of VX before the shift."""
        print(f"Shifting V{self.opcode & 0x0F00 >> 8} left by one")
        self.V[0xF] = (self.V[self.opcode & 0x0F00 >> 8] >> 7) & 0x1
        self.V[self.opcode & 0x0F00 >> 8] <<= 1
        self.pc += 2

    def opcode_9xxx(self):
        """Skips the next instruction if VX doesn't equal VY."""
        print(f"Comparing V{self.opcode & 0x0F00 >> 8} to V{self.opcode & 0x00F0 >> 4}")
        if self.V[self.opcode & 0x0F00 >> 8] != self.V[self.opcode & 0x00F0 >> 4]:
            self.pc += 2

    def opcode_Axxx(self):
        """Sets I to the address NNN."""
        print(f"Setting I to {hex(self.opcode & 0x0FFF)}")
        self.I = self.opcode & 0x0FFF
        self.pc += 2

    def opcode_Bxxx(self):
        """Jumps to the address NNN plus V0."""
        print(f"Jumping to address {hex(self.opcode & 0x0FFF)} plus V0")
        self.pc = self.V[0] + (self.opcode & 0x0FFF)

    def opcode_Cxxx(self):
        """Sets VX to the result of a bitwise AND operation on a random number and NN."""
        print(
            f"Setting V{self.opcode & 0x0F00 >> 8} to a random number AND {hex(self.opcode & 0x00FF)}"
        )
        self.V[self.opcode & 0x0F00 >> 8] = random.randint(0, 255) & (
            self.opcode & 0x00FF
        )
        self.pc += 2

    def opcode_Dxxx(self):
        """Draws a sprite at coordinate (VX, VY) with width of 8 pixels and height of N pixels."""
        print(
            f"Drawing a sprite at ({self.V[self.opcode & 0x0F00 >> 8]}, {self.V[self.opcode & 0x00F0 >> 4]}) with width of 8 pixels and height of {self.opcode & 0x000F}"
        )
        x = self.V[self.opcode & 0x0F00 >> 8] % 64  # X coordinate
        y = self.V[self.opcode & 0x00F0 >> 4] % 32  # Y coordinate
        height = self.opcode & 0x000F  # Height of the sprite
        self.V[0xF] = 0  # Reset VF
        for yline in range(height):  # Each sprite is N pixels tall
            pixel = self.memory[self.I + yline]  # Get the current line of the sprite
            for xline in range(8):  # Each sprite is 8 pixels wide
                if (pixel & (0x80 >> xline)) != 0:  # If the current pixel is on
                    dx = (x + xline) % 64  # Wrap around the screen
                    dy = (y + yline) % 32  # Wrap around the screen
                    if self.display[dy][dx] == 1:  # If the pixel is already on
                        self.V[0xF] = 1  # Set VF to 1
                    self.display[dy][dx] ^= 1  # XOR the pixel
        self.pc += 2

    def opcode_Exxx(self):
        """Calls a more specific opcode function based on the last two nibbles."""
        print(f"Calling opcode function Exxx")
        self.opcode_table_Exxx[self.opcode & 0x00FF]()
        self.pc += 2

    def opcode_Ex9E(self):
        """Skips the next instruction if the key stored in VX is pressed."""
        print(f"Checking if V{self.opcode & 0x0F00 >> 8} is pressed")
        if self.key[self.V[self.opcode & 0x0F00 >> 8]] != 0:  # If the key is pressed
            self.pc += 2  # Skip the next instruction

    def opcode_ExA1(self):
        """Skips the next instruction if the key stored in VX isn't pressed."""
        print(f"Checking if V{self.opcode & 0x0F00 >> 8} is not pressed")
        if (
            self.key[self.V[self.opcode & 0x0F00 >> 8]] == 0
        ):  # If the key is not pressed
            self.pc += 2  # Skip the next instruction

    def opcode_Fxxx(self):
        """Calls a more specific opcode function based on the last two nibbles."""
        print(f"Calling opcode function Fxxx")
        func = self.opcode_table_Fxxx.get(
            self.opcode & 0x00FF
        )  # Get the function from the table
        if func:
            func()  # Call the function
        else:
            logging.error(
                f"Unknown opcode {hex(self.opcode)} at address {hex(self.pc - 2)}"
            )
        self.pc += 2

    def opcode_Fx07(self):
        """Sets VX to the value of the delay timer."""
        print(f"Setting V{self.opcode & 0x0F00 >> 8} to the value of the delay timer")
        self.V[self.opcode & 0x0F00 >> 8] = (
            self.delay_timer & 0xFF
        )  # Ensure Vx stays 8-bit
        self.pc += 2

    def opcode_Fx0A(self):
        """Wait for a key press, store the value of the key in Vx."""
        print(f"Waiting for a key press and storing it in V{self.opcode & 0x0F00 >> 8}")
        self.waiting_for_keypress = True  # Set the flag
        self.key_register = (self.opcode & 0x0F00) >> 8  # Store the register
        self.pc += 2

    def opcode_Fx15(self):
        """Sets the delay timer to VX."""
        print(f"Setting the delay timer to V{self.opcode & 0x0F00 >> 8}")
        self.delay_timer = (
            self.V[self.opcode & 0x0F00 >> 8] & 0xFF
        )  # Ensure Vx stays 8-bit
        self.pc += 2

    def opcode_Fx18(self):
        """Sets the sound timer to VX."""
        print(f"Setting the sound timer to V{self.opcode & 0x0F00 >> 8}")
        self.sound_timer = (
            self.V[self.opcode & 0x0F00 >> 8] & 0xFF
        )  # Ensure Vx stays 8-bit
        self.pc += 2

    def opcode_Fx1E(self):
        """Adds VX to I and sets VF to 1 if there's an overflow."""
        print(f"Adding V{self.opcode & 0x0F00 >> 8} to I")
        self.I += self.V[self.opcode & 0x0F00 >> 8]
        if self.I > 0xFFF:
            self.V[0xF] = 1
        else:
            self.V[0xF] = 0
        self.pc += 2

    def opcode_Fx29(self):
        """Sets I to the location of the sprite for the character in VX."""
        print(
            f"Setting I to the location of the sprite for V{self.opcode & 0x0F00 >> 8}"
        )
        self.I = self.V[self.opcode & 0x0F00 >> 8] * 0x5  # Each sprite is 5 bytes long
        self.pc += 2

    def opcode_Fx33(self):
        """Stores the binary-coded decimal representation of VX at the addresses I, I+1, and I+2."""
        print(
            f"Storing the BCD representation of V{self.opcode & 0x0F00 >> 8} at addresses I, I+1, and I+2"
        )
        self.memory[self.I] = self.V[self.opcode & 0x0F00 >> 8] // 100  # Hundreds
        self.memory[self.I + 1] = (self.V[self.opcode & 0x0F00 >> 8] // 10) % 10  # Tens
        self.memory[self.I + 2] = (self.V[self.opcode & 0x0F00 >> 8] % 100) % 10  # Ones
        self.pc += 2

    def opcode_Fx55(self):
        """Store registers V0 through Vx in memory starting at location I."""
        print(
            f"Storing V0 through V{self.opcode & 0x0F00 >> 8} in memory starting at address I"
        )
        x = (self.opcode & 0x0F00) >> 8  # X register
        for i in range(x + 1):  # Store V0 through Vx in memory starting at address I
            self.memory[self.I + i] = self.V[i]

    def opcode_Fx65(self):
        """Read registers V0 through Vx from memory starting at location I."""
        print(
            f"Reading V0 through V{self.opcode & 0x0F00 >> 8} from memory starting at address I"
        )
        x = (self.opcode & 0x0F00) >> 8  # X register
        for i in range(x + 1):  # Read V0 through Vx from memory starting at address I
            self.V[i] = self.memory[self.I + i]
        self.pc += 2

    def emulate_cycle(self):
        """Emulates one cycle of the CHIP-8 CPU."""
        self.fetch_opcode()
        self.execute_opcode()

        # Delay timer and sound timer should be updated at a rate of 60Hz
        # If your main loop is running faster than 60Hz, you may need to call this less frequently
        current_time = time.time()
        if current_time - self.last_timer_update >= 1 / 60:  # 60Hz
            self.update_timers()  # Update the timers
            self.last_timer_update = current_time  # Reset the timer

    def update_timers(self):
        """Updates the delay and sound timers."""
        if self.delay_timer > 0:  # If the delay timer is on
            self.delay_timer -= 1  # Decrement the delay timer

        if self.sound_timer > 0:  # If the sound timer is on
            self.sound_timer -= 1  # Decrement the sound timer
            if self.sound_timer == 1:  # If the sound timer is about to turn off
                print("BEEP!")

    def set_keys(self):
        """Sets the key state based on the current state of the keyboard."""
        keys = pygame.key.get_pressed()
        key_map = {
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
        for key, value in key_map.items():
            self.key[value] = 1 if keys[key] else 0

    def draw_graphics(self):
        """Draws the current display state to the screen."""
        scale = 10  # Scale factor for each pixel
        self.display_surface.fill((44, 53, 0))  # Clear the screen with black

        for x in range(64):  # The display is 64x32 pixels
            for y in range(32):  # The display is 64x32 pixels
                if self.display[y][x] == 1:  # If the pixel is on
                    print(f"Drawing pixel at ({x}, {y})")
                    pygame.draw.rect(
                        self.display_surface,
                        (25, 32, 11),
                        (x * scale, y * scale, scale, scale),
                    )  # Draw a white rectangle
        pygame.display.flip()  # Update the full display

    def print_registers(self):
        """Prints the current state of the registers to the console."""
        logging.debug("Register state:")
        for i, v in enumerate(self.V):  # Print all the registers
            logging.info(f"V{i:X}: {v:02X}")  # Print the register in hex
        logging.debug(f"I: {self.I:03X}")  # Print I in hex
        logging.debug(f"PC: {self.pc:03X}")  # Print PC in hex
        logging.debug(f"SP: {self.sp:02X}")  # Print SP in hex

    def load_game(self, filename):
        """Loads a CHIP-8 game into memory."""
        print("Loading game: " + filename)
        with open(filename, "rb") as game:
            game_data = game.read()
            print(len(game_data))
            print(f"Loading game into memory at address 0x200.")
            for i, byte in enumerate(game_data):
                self.memory[0x200 + i] = byte

    def main_loop(self):
        """Main loop of the emulator."""
        running = True
        while running:
            print(f"PC: {hex(self.pc)}")
            print(f"I: {hex(self.I)}")
            print(f"SP: {hex(self.sp)}")
            print(f"V0: {hex(self.V[0])}")
            print(f"V1: {hex(self.V[1])}")
            print(f"V2: {hex(self.V[2])}")
            print(f"V3: {hex(self.V[3])}")
            print(f"V4: {hex(self.V[4])}")
            print(f"V5: {hex(self.V[5])}")
            print(f"V6: {hex(self.V[6])}")
            print(f"V7: {hex(self.V[7])}")
            print(f"V8: {hex(self.V[8])}")
            print(f"V9: {hex(self.V[9])}")
            print(f"VA: {hex(self.V[10])}")
            print(f"VB: {hex(self.V[11])}")
            print(f"VC: {hex(self.V[12])}")
            print(f"VD: {hex(self.V[13])}")
            print(f"VE: {hex(self.V[14])}")
            print(f"VF: {hex(self.V[15])}")
            print(f"Delay timer: {hex(self.delay_timer)}")
            print(f"Sound timer: {hex(self.sound_timer)}")
            print(f"Waiting for keypress: {self.waiting_for_keypress}")
            if self.key_register is not None:
                print(f"Key register: {hex(self.key_register)}")
            else:
                print("Key register: None")
            print(f"Key state: {self.key}")
            print(f"Stack: {self.stack}")
            # print(f"Display: {self.display}")
            # print(f"Memory: {self.memory}")
            print(f"Opcode: {hex(self.opcode)}")
            print(f"Opcode table: {self.opcode_table}")

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if self.waiting_for_keypress:
                        for key, value in self.key_map.items():
                            if event.key == key:
                                self.V[self.key_register] = value
                                self.waiting_for_keypress = False
                                break

            if not self.waiting_for_keypress:
                self.emulate_cycle()

            self.set_keys()
            self.draw_graphics()
            time.sleep(1 / 60)  # Limit to 60 Hz

        pygame.quit()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python chip8.py [ROM file]")
        sys.exit(1)
    game_filename = sys.argv[1]
    chip8 = Chip8(game_filename)
    chip8.main_loop()
