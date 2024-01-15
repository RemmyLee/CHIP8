# A CHIP8 Emulator written in Python

import time
import pygame
import logging
import random
import sys
from OpenGL.GL import *
from OpenGL.GLUT import *

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Chip8:
    def __init__(self, filename):
        pygame.init()
        self.window_width, self.window_height = 640, 320  # Adjust as needed
        pygame.display.set_mode(
            (self.window_width, self.window_height), pygame.DOUBLEBUF | pygame.OPENGL
        )

        # Set up OpenGL context
        glClearColor(0.44, 0.53, 0.0, 1.0)  # Black background
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, 64, 32, 0, -1, 1)  # Coordinate system setup
        glMatrixMode(GL_MODELVIEW)
        pygame.display.set_caption(f"CHIP-8 Emulator: {filename}")

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
        self.display = [[0 for _ in range(64)] for _ in range(32)]  # Display state
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
            # Load the fontset into memory at 0x50
            self.memory[0x50 + i] = fontset[i]

    def fetch_opcode(self):
        """Fetches the next opcode from memory and increments the program counter."""
        print(f"Fetching opcode from address {hex(self.pc)}")
        self.opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]
        print(hex(self.opcode))
        self.pc += 2

    def execute_opcode(self):
        # pdb.set_trace()
        """Calls a more specific opcode function based on the first nibble."""
        print(f"Executing opcode {hex(self.opcode)}")
        self.opcode_table[self.opcode & 0xF000]()
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1

    def opcode_0xxx(self):
        """Calls a more specific opcode function based on the last two nibbles."""
        print(f"Calling opcode function {hex(self.opcode & 0x00FF)}")
        opcode = self.opcode & 0x00FF
        if opcode in self.opcode_table_0xxx:
            self.opcode_table_0xxx[opcode]()

    def opcode_00E0(self):  # CLS
        """Clear the display.
        We can simply set the entire video buffer to zeroes."""
        print(f"Clearing the screen")
        self.display = [[0 for _ in range(64)] for _ in range(32)]

    def opcode_00EE(self):  # RET
        """Return from a subroutine.
        The top of the stack has the address of one instruction past the one that called the subroutine,
        so we can put that back into the PC. Note that this overwrites our preemptive pc += 2 earlier.
        """
        print(f"Returning from a subroutine")
        self.sp -= 1  # Decrement stack pointer
        self.pc = self.stack[self.sp]  # Return to the stored address

    def opcode_1xxx(self):  # JP addr
        """Jump to location nnn.
        The interpreter sets the program counter to nnn.
        A jump doesn’t remember its origin, so no stack interaction required."""
        print(f"Jumping to address {hex(self.opcode & 0x0FFF)}")
        self.pc = self.opcode & 0x0FFF  # Set PC to NNN
        print(f"PC = {hex(self.pc)}")

    def opcode_2xxx(self):  # CALL addr
        """Call subroutine at nnn.
        When we call a subroutine, we want to return eventually, so we put the
        current PC onto the top of the stack. Remember that we did pc += 2 in Cycle(),
        so the current PC holds the next instruction after this CALL, which is correct.
        We don’t want to return to the CALL instruction because it would be an infinite
        loop of CALLs and RETs."""
        print(f"Calling subroutine at address {hex(self.opcode & 0x0FFF)}")
        self.stack[self.sp] = self.pc  # Store current address on the stack
        self.sp += 1  # Increment stack pointer
        self.pc = self.opcode & 0x0FFF  # Jump to the subroutine

    def opcode_3xxx(self):  # SE Vx, byte
        """Skip next instruction if Vx = kk.
        Since our PC has already been incremented by 2 in Cycle(),
        we can just increment by 2 again to skip the next instruction.
        """
        print(f"Comparing V{self.opcode & 0x0F00 >> 8} to {hex(self.opcode & 0x00FF)}")
        if self.V[(self.opcode & 0x0F00) >> 8] == (self.opcode & 0x00FF):
            print(f"Opcode = {hex(self.opcode)}")
            self.pc += 2
        else:
            print(f"Opcode = {hex(self.opcode)}")

    def opcode_4xxx(self):  # SNE Vx, byte
        """Skip next instruction if Vx != kk.
        Since our PC has already been incremented by 2 in Cycle(),
        we can just increment by 2 again to skip the next instruction."""
        print(f"Comparing V{self.opcode & 0x0F00 >> 8} to {hex(self.opcode & 0x00FF)}")
        if self.V[self.opcode & 0x0F00 >> 8] != (self.opcode & 0x00FF):
            return

    def opcode_5xxx(self):  # SE Vx, Vy
        """Skip next instruction if Vx = Vy.
        Since our PC has already been incremented by 2 in Cycle(),
        we can just increment by 2 again to skip the next instruction."""
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        n = self.opcode & 0x000F

        print(f"Comparing V{x} to V{y}")

        # Check if the last nibble 'n' is 0x0; if not, it's an invalid opcode
        if n != 0x0:
            raise ValueError(f"Invalid opcode: {hex(self.opcode)}")

        # Skip the next instruction if VX equals VY
        if self.V[x] == self.V[y]:
            self.pc += 2

    def opcode_6xxx(self):  # LD Vx, byte
        """Sets VX to NN."""
        x = (self.opcode & 0x0F00) >> 8  # Get the register index (x)
        nn = self.opcode & 0x00FF  # Get the byte value (nn)
        self.V[x] = nn  # Set VX to NN
        print(f"Setting V{x} to {hex(nn)}")

    def opcode_7xxx(self):  # ADD Vx, byte
        """Adds NN to VX (carry flag is not changed)."""
        x = (self.opcode & 0x0F00) >> 8  # Get the register index
        nn = self.opcode & 0x00FF  # Get the value
        print(f"Adding {hex(nn)} to V{x}")
        self.V[x] = self.V[x] + nn  # Add NN to VX

    def opcode_8xxx(
        self,
    ):  # Calls a more specific opcode function based on the last nibble.
        """Calls a more specific opcodeself.I = self.opcode & 0x0FFF  # Set I to NNN function based on the last nibble."""
        print(f"Calling opcode function 8xxx")
        self.opcode_table_8xxx.get(self.opcode & 0x000F)
        self.pc += 2

    def opcode_8xy0(self):  # LD Vx, Vy
        """Sets VX to the value of VY."""
        print(f"Setting V{self.opcode & 0x0F00 >> 8} to V{self.opcode & 0x00F0 >> 4}")
        x = (self.opcode & 0x0F00) >> 8  # Get the register index
        y = (self.opcode & 0x00F0) >> 4
        self.V[x] = self.V[y]  # Set VX to the value of VY

    def opcode_8xy1(self):  # OR Vx, Vy
        """Sets VX to VX OR VY."""
        print(f"Setting V{self.opcode & 0x0F00 >> 8} to V{self.opcode & 0x00F0 >> 4}")
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        self.V[x] |= self.V[y]

    def opcode_8xy2(self):  # AND Vx, Vy
        """Sets VX to VX AND VY."""
        print(f"Setting V{self.opcode & 0x0F00 >> 8} to V{self.opcode & 0x00F0 >> 4}")
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        self.V[x] &= self.V[y]

    def opcode_8xy3(self):  # XOR Vx, Vy
        """Sets VX to VX XOR VY."""
        print(f"Setting V{self.opcode & 0x0F00 >> 8} to V{self.opcode & 0x00F0 >> 4}")
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        self.V[x] ^= self.V[y]

    def opcode_8xy4(self):  # ADD Vx, Vy
        """Set Vx = Vx + Vy, set VF = carry.
        The values of Vx and Vy are added together. If the result is greater
        than 8 bits (i.e., > 255,) VF is set to 1, otherwise 0. Only the lowest
        8 bits of the result are kept, and stored in Vx.

        This is an ADD with an overflow flag. If the sum is greater than what can
        fit into a byte (255), register VF will be set to 1 as a flag."""
        print(f"Adding V{self.opcode & 0x00F0 >> 4} to V{self.opcode & 0x0F00 >> 8}")
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        self.V[x] += self.V[y]
        if self.V[x] > 0xFF:
            self.V[0xF] = 1
        else:
            self.V[0xF] = 0
        self.V[x] &= 0xFF

    def opcode_8xy5(self):  # SUB Vx, Vy
        """Set Vx = Vx - Vy, set VF = NOT borrow.
        If Vx > Vy, then VF is set to 1, otherwise 0. Then Vy is subtracted from Vx,
        and the results stored in Vx."""
        print(
            f"Subtracting V{self.opcode & 0x00F0 >> 4} from V{self.opcode & 0x0F00 >> 8}"
        )
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        if self.V[x] > self.V[y]:
            self.V[0xF] = 1
        else:
            self.V[0xF] = 0
        self.V[x] -= self.V[y]

        print(f"V{x} = {self.V[x]}")

    def opcode_8xy6(self):
        """Set Vx = Vx SHR 1.
        If the least-significant bit of Vx is 1, then VF is set to 1, otherwise 0.
        Then Vx is divided by 2.
        """
        x = (self.opcode & 0x0F00) >> 8  # Get the register index
        time.sleep(3)
        print(f"Shifting V{x} right by 1")
        self.V[0xF] = self.V[x] & 0x1  # Store the least significant bit of Vx in VF
        time.sleep(3)
        print(f"V{x} = {self.V[x]}")
        self.V[x] >>= 1  # Divide Vx by 2
        time.sleep(3)
        print(f"V{x} = {self.V[x]}")
        print(f"VF = {self.V[0xF]}")
        print("--------------------")

    def opcode_8xy7(self):  # SUBN Vx, Vy
        """Set Vx = Vy - Vx, set VF = NOT borrow.
        If Vy > Vx, then VF is set to 1, otherwise 0. Then Vx is subtracted from Vy, and the results stored in Vx.
        """
        print(
            f"Subtracting V{self.opcode & 0x0F00 >> 8} from V{self.opcode & 0x00F0 >> 4}"
        )
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        if self.V[y] > self.V[x]:
            self.V[0xF] = 1
        else:
            self.V[0xF] = 0
        self.V[x] = self.V[y] - self.V[x]

    def opcode_8xyE(
        self,
    ):  # SHL Vx {, Vy}
        """Set Vx = Vx SHL 1.
        If the most-significant bit of Vx is 1, then VF is set to 1, otherwise to 0. Then Vx is multiplied by 2.
        A left shift is performed (multiplication by 2), and the most significant bit is saved in Register VF.
        """
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        self.V[0xF] = self.V[x] >> 7  # Store the most significant bit in VF
        self.V[x] <<= 1 & 0xFF  # Multiply VX by 2

    def opcode_9xxx(self):  # SNE Vx, Vy
        """Skip next instruction if Vx != Vy.
        Since our PC has already been incremented by 2 in Cycle(), we can just increment by 2 again to skip the next instruction.
        """
        x = (self.opcode & 0x0F00) >> 8  # Get the register index
        y = (self.opcode & 0x00F0) >> 4  # Get the register index
        # Skip the next instruction if VX doesn't equal VY
        if self.V[x] != self.V[y]:
            return

    def opcode_Axxx(self):  # LD I, addr
        """Sets I to the address NNN."""
        print(f"Setting I to {hex(self.opcode & 0x0FFF)}")
        self.I = self.opcode & 0x0FFF  # Set I to NNN

    def opcode_Bxxx(self):
        print(f"Jumping to address {hex(self.opcode & 0x0FFF)} plus V0")
        self.pc = self.V[0] + (self.opcode & 0x0FFF)  # Jump to NNN + V0

    def opcode_Cxxx(
        self,
    ):  # RND Vx, byte
        """Sets VX to the result of a bitwise AND operation on a random number and NN."""
        print(
            f"Setting V{self.opcode & 0x0F00 >> 8} to a random number AND {hex(self.opcode & 0x00FF)}"
        )
        x = (self.opcode & 0x0F00) >> 8  # Get the register index
        byte = self.opcode & 0x00FF  # Get the value
        self.V[x] = random.randint(0, 255) & byte  # Generate a random number and AND it

    def opcode_Dxxx(
        self,
    ):  # DRW Vx, Vy, nibble
        """Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.
        We iterate over the sprite, row by row and column by column. We know there are eight columns
        because a sprite is guaranteed to be eight pixels wide.
        If a sprite pixel is on then there may be a collision with what’s already being displayed,
        so we check if our screen pixel in the same location is set. If so we must set the VF register to express collision.
        Then we can just XOR the screen pixel with 0xFFFFFFFF to essentially XOR it with the sprite pixel (which we now know is on).
        We can’t XOR directly because the sprite pixel is either 1 or 0 while our video pixel is either 0x00000000 or 0xFFFFFFFF.
        """
        print(
            f"Drawing a sprite at ({self.V[self.opcode & 0x0F00 >> 8]}, {self.V[self.opcode & 0x00F0 >> 4]}) with width of 8 pixels and height of {self.opcode & 0x000F}"
        )
        x = self.V[(self.opcode & 0x0F00) >> 8] % 64  # X coordinate
        y = self.V[(self.opcode & 0x00F0) >> 4] % 32  # Y coordinate
        height = self.opcode & 0x000F  # Height of the sprite
        self.V[0xF] = 0  # Reset VF

        for yline in range(height):  # Each sprite is N pixels tall
            pixel = self.memory[self.I + yline]  # Get the current line of the sprite

            for xline in range(8):  # Each sprite is 8 pixels wide
                if (pixel & (0x80 >> xline)) != 0:  # If the current pixel is on
                    dx = (x + xline) % 64  # Wrap around the screen horizontally
                    dy = (y + yline) % 32  # Wrap around the screen vertically

                    if self.display[dy][dx] == 1:  # If the pixel is already on
                        self.V[0xF] = 1  # Set VF to 1 (collision)
                    self.display[dy][dx] ^= 1  # XOR the pixel

    def opcode_Exxx(self):
        """Calls a more specific opcode function based on the last two nibbles."""
        print(f"Calling opcode function Exxx")
        self.opcode_table_Exxx[self.opcode & 0x00FF]()

    def opcode_Ex9E(self):  # SKP Vx
        """Skip next instruction if key with the value of Vx is pressed.
        Since our PC has already been incremented by 2 in Cycle(), we can just increment by 2 again to skip the next instruction.
        """
        print(f"Calling opcode function Exxx")
        x = (self.opcode & 0x0F00) >> 8  # Get the register index
        key = self.V[x]  # Get the value of the register
        if self.key[key]:  # If the key is pressed
            self.pc += 2

    def opcode_ExA1(self):  # SKNP Vx
        """Skip next instruction if key with the value of Vx is not pressed.
        Since our PC has already been incremented by 2 in Cycle(), we can just increment by 2 again to skip the next instruction.
        """
        print(f"Checking if V{self.opcode & 0x0F00 >> 8} is not pressed")
        x = (self.opcode & 0x0F00) >> 8  # Get the register index
        key = self.V[x]  # Get the value of the register
        if not self.key[key]:  # If the key is not pressed
            self.pc += 2

    def opcode_Fxxx(self):
        """Calls a more specific opcode function based on the last two nibbles."""
        print(f"Calling opcode function Fxxx")
        func = self.opcode_table_Fxxx.get(
            self.opcode & 0x00FF
        )  # Get the function from the table
        if func:
            func()  # Call the function

    def opcode_Fx07(self):  # LD Vx, DT
        """Sets VX to the value of the delay timer."""
        print(f"Setting V{self.opcode & 0x0F00 >> 8} to the value of the delay timer")
        x = (self.opcode & 0x0F00) >> 8  # Get the register index
        self.V[x] = self.delay_timer  # Set VX to the value of the delay timer

    def opcode_Fx0A(self):  # LD Vx, K
        """Wait for a key press, store the value of the key in Vx.
        The easiest way to “wait” is to decrement the PC by 2 whenever a keypad value is not detected. This has the effect of
        running the same instruction repeatedly."""
        print(f"Waiting for a key press and storing it in V{self.opcode & 0x0F00 >> 8}")
        x = (self.opcode & 0x0F00) >> 8
        key_pressed = False
        for i in range(16):
            if self.key[i]:
                self.V[x] = i
                key_pressed = True
                break
        if not key_pressed:
            self.pc -= 2  # Stay at the current instruction if no key is pressed

    def opcode_Fx15(self):  # LD DT, Vx
        """Sets the delay timer to VX."""
        print(f"Setting the delay timer to V{self.opcode & 0x0F00 >> 8}")
        x = (self.opcode & 0x0F00) >> 8  # Get the register index
        self.delay_timer = self.V[x]  # Set the delay timer to the value of the register

    def opcode_Fx18(self):  # LD ST, Vx
        """Sets the sound timer to VX."""
        print(f"Setting the sound timer to V{self.opcode & 0x0F00 >> 8}")
        x = (self.opcode & 0x0F00) >> 8  # Get the register index
        self.sound_timer = self.V[x]  # Set the sound timer to the value of the register

    def opcode_Fx1E(self):  # ADD I, Vx
        """Adds VX to I and sets VF to 1 if there's an overflow."""
        print(f"Adding V{self.opcode & 0x0F00 >> 8} to I")
        x = (self.opcode & 0x0F00) >> 8  # Get the register index
        self.I += self.V[x]

    def opcode_Fx29(
        self,
    ):  # LD F, Vx
        """Set I = location of sprite for digit Vx.
        We know the font characters are located at 0x50, and we know they’re five bytes each, so we can get
        the address of the first byte of any character by taking an offset from the start address.
        """
        print(
            f"Setting I to the location of the sprite for V{self.opcode & 0x0F00 >> 8}"
        )
        x = (self.opcode & 0x0F00) >> 8  # Get the register index
        digit = self.V[x]  # Get the value of the register
        self.I = 0x50 + (5 * digit)  # Set I to the location of the sprite

    def opcode_Fx33(self):  # LD B, Vx
        """Store BCD representation of Vx in memory locations I, I+1, and I+2.
        The interpreter takes the decimal value of Vx, and places the hundreds digit in memory at location in I, the tens
        digit at location I+1, and the ones digit at location I+2.
        We can use the modulus operator to get the right-most digit of a number, and then do a division to remove that digit.
        A division by ten will either completely remove the digit (340 / 10 = 34), or result in a float which will be truncated
        (345 / 10 = 34.5 = 34)."""
        print(
            f"Storing the BCD representation of V{self.opcode & 0x0F00 >> 8} at addresses I, I+1, and I+2"
        )
        x = (self.opcode & 0x0F00) >> 8  # Get the register index
        value = self.V[x]  # Get the value of the register
        self.memory[self.I] = value // 100  # Get the left-most digit
        self.memory[self.I + 1] = (value // 10) % 10  # Get the middle digit
        self.memory[self.I + 2] = (value % 100) % 10  # Get the right-most digit

    def opcode_Fx55(self):  # LD [I], Vx
        """Stores V0 to VX in memory starting at address I."""
        x = (self.opcode & 0x0F00) >> 8
        for i in range(x + 1):
            self.memory[self.I + i] = self.V[i]

    def opcode_Fx65(self):  # LD Vx, [I]
        """Fills V0 to VX with values from memory starting at address I."""
        x = (self.opcode & 0x0F00) >> 8
        for i in range(x + 1):
            self.V[i] = self.memory[self.I + i]

    def emulate_cycle(self):  # Emulates one cycle of the CHIP-8 CPU
        """Emulates one cycle of the CHIP-8 CPU."""
        if self.waiting_for_keypress:  # If the emulator is waiting for a key press
            return  # Skip the cycle
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
        key_map = self.key_map
        for key, value in key_map.items():
            self.key[value] = 1 if keys[key] else 0

    def draw_graphics(self):
        """Draws the current display state to the screen using OpenGL."""
        glClear(GL_COLOR_BUFFER_BIT)

        glColor3f(0.25, 0.32, 0.11)  # Color for 'on' pixels (adjust as needed)

        scaling_factor = 1  # Scaling factor from 64x32 to 640x320

        glBegin(GL_QUADS)
        for x in range(64):  # The display is 64x32 pixels
            for y in range(32):
                if self.display[y][x] == 1:  # If the pixel is on
                    # Draw a scaled rectangle (quad) for each 'on' pixel
                    glVertex2f(x * scaling_factor, y * scaling_factor)
                    glVertex2f((x + 1) * scaling_factor, y * scaling_factor)
                    glVertex2f((x + 1) * scaling_factor, (y + 1) * scaling_factor)
                    glVertex2f(x * scaling_factor, (y + 1) * scaling_factor)
        glEnd()

        pygame.display.flip()

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
            print(f"Opcode: {hex(self.opcode)}")
            print(f"I: {hex(self.I)}")
            print(f"SP: {hex(self.sp)}")
            print(f"Delay timer: {hex(self.delay_timer)}")
            print(f"Sound timer: {hex(self.sound_timer)}")
            if self.key_register is not None:
                print(f"Key register: {hex(self.key_register)}")
            else:
                print("Key register: None")

            for event in pygame.event.get():  # Check for events
                if event.type == pygame.QUIT:  # If the user clicks the close button
                    running = False  # Stop the main loop
                elif event.type == pygame.KEYDOWN:  # If the user presses a key
                    if (
                        self.waiting_for_keypress
                    ):  # If the emulator is waiting for a key press
                        for (
                            key,
                            value,
                        ) in self.key_map.items():  # Loop through the key map
                            if event.key == key:  # If the key pressed is in the key map
                                self.V[
                                    self.key_register
                                ] = value  # Store the key in the register
                                self.waiting_for_keypress = False  # Reset the flag
                                break

            if not self.waiting_for_keypress:
                self.emulate_cycle()

            self.set_keys()
            self.draw_graphics()
            time.sleep(0.0015)  # Limit to 60 Hz
            # time.sleep(1)

        pygame.quit()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python chip8.py [ROM file]")
        sys.exit(1)
    game_filename = sys.argv[1]
    chip8 = Chip8(game_filename)
    chip8.main_loop()
