import random
import time


class Chip8CPU:
    def __init__(self):
        self.memory = [0] * 4096
        self.V = [0] * 16  # CPU registers
        self.I = 0  # Index register
        self.pc = 0x200  # Program counter starts at 0x200
        self.stack = [0] * 16
        self.sp = -1  # Stack pointer
        self.delay_timer = 0
        self.sound_timer = 0
        self.display = [[0 for _ in range(64)] for _ in range(32)]
        self.waiting_for_keypress = False
        self.key_register = None
        self.opcode = 0
        self.last_timer_update = time.time()
        self.load_fontset()

        self.opcode_table = {
            0x0000: self.opcode_0xxx,
            0x1000: self.opcode_1xxx,
            0x2000: self.opcode_2xxx,
            0x3000: self.opcode_3xxx,
            0x4000: self.opcode_4xxx,
            0x5000: self.opcode_5xxx,
            0x6000: self.opcode_6xxx,
            0x7000: self.opcode_7xxx,
            0x8000: self.opcode_8xxx,
            0x9000: self.opcode_9xxx,
            0xA000: self.opcode_Axxx,
            0xB000: self.opcode_Bxxx,
            0xC000: self.opcode_Cxxx,
            0xD000: self.opcode_Dxxx,
            0xE000: self.opcode_Exxx,
            0xF000: self.opcode_Fxxx,
        }
        self.opcode_table_0xxx = {
            0x00E0: self.opcode_00E0,
            0x00EE: self.opcode_00EE,
        }
        self.opcode_table_8xxx = {
            0x0000: self.opcode_8xy0,
            0x0001: self.opcode_8xy1,
            0x0002: self.opcode_8xy2,
            0x0003: self.opcode_8xy3,
            0x0004: self.opcode_8xy4,
            0x0005: self.opcode_8xy5,
            0x0006: self.opcode_8xy6,
            0x0007: self.opcode_8xy7,
            0x000E: self.opcode_8xyE,
        }
        self.opcode_table_Exxx = {
            0x009E: self.opcode_Ex9E,
            0x00A1: self.opcode_ExA1,
        }
        self.opcode_table_Fxxx = {
            0x0007: self.opcode_Fx07,
            0x000A: self.opcode_Fx0A,
            0x0015: self.opcode_Fx15,
            0x0018: self.opcode_Fx18,
            0x001E: self.opcode_Fx1E,
            0x0029: self.opcode_Fx29,
            0x0033: self.opcode_Fx33,
            0x0055: self.opcode_Fx55,
            0x0065: self.opcode_Fx65,
        }

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
            self.memory[0x50 + i] = fontset[i]  # Load the fontset into memory

    def load_game(self, filename):
        with open(filename, "rb") as game:
            game_data = game.read()
            for i, byte in enumerate(game_data):
                self.memory[0x200 + i] = byte
        print(f"Loaded {len(game_data)} bytes into memory")

    def emulate_cycle(self):
        if not self.waiting_for_keypress:
            self.fetch_opcode()
            self.execute_opcode()

        current_time = time.time()
        if current_time - self.last_timer_update >= 1 / 60:
            self.update_timers()
            self.last_timer_update = current_time
        # time.sleep(1)  # Adjust as needed for your system

    def fetch_opcode(self):
        self.opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]
        print(f"Fetched opcode {self.opcode:04X} at address {self.pc:04X}")

    def execute_opcode(self):
        # Extracting the relevant bits of the opcode
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        n = self.opcode & 0x000F
        nn = self.opcode & 0x00FF
        nnn = self.opcode & 0x0FFF

        if self.opcode == 0x00E0:
            self.display = [[0 for _ in range(64)] for _ in range(32)]
            self.pc += 2
            print("Clearing the display")

        elif self.opcode == 0x00EE:
            self.sp -= 1
            self.pc = self.stack[self.sp]
            self.pc += 2
            print("Returning from a subroutine")

        elif self.opcode & 0xF000 == 0x0000:
            self.pc += 2
            print("Ignoring NOP")

        elif self.opcode & 0xF000 == 0x1000:
            self.pc = nnn
            print(f"Jumping to address {nn}")

        elif self.opcode & 0xF000 == 0x2000:
            self.stack[self.sp] = self.pc
            self.sp += 1
            self.pc = nnn
            print(f"Calling subroutine at address {nn}")

        elif self.opcode & 0xF000 == 0x3000:
            if self.V[x] == nn:
                self.pc += 4
            else:
                self.pc += 2
            print(f"Skipping next instruction if V[{x}] == {nn}")

        elif self.opcode & 0xF000 == 0x4000:
            if self.V[x] != nn:
                self.pc += 4
            else:
                self.pc += 2
            print(f"Skipping next instruction if V[{x}] != {nn}")

        elif self.opcode & 0xF00F == 0x5000:
            if self.V[x] == self.V[y]:
                self.pc += 4
            else:
                self.pc += 2
            print(f"Skipping next instruction if V[{x}] == V[{y}]")
        elif self.opcode & 0xF000 == 0x6000:
            self.V[x] = nn
            self.pc += 2
            print(f"Setting V[{x}] to {nn}")
        elif self.opcode & 0xF000 == 0x7000:
            self.V[x] += nn
            self.pc += 2
            print(f"Adding {nn} to V[{x}]")
        elif self.opcode & 0xF00F == 0x8000:
            self.V[x] = self.V[y]
            self.pc += 2
            print(f"Setting V[{x}] to V[{y}]")
        elif self.opcode & 0xF00F == 0x8001:
            self.V[x] |= self.V[y]
            self.pc += 2
            print(f"Setting V[{x}] to V[{x}] | V[{y}]")
        elif self.opcode & 0xF00F == 0x8002:
            self.V[x] &= self.V[y]
            self.pc += 2
            print(f"Setting V[{x}] to V[{x}] & V[{y}]")
        elif self.opcode & 0xF00F == 0x8003:
            self.V[x] ^= self.V[y]
            self.pc += 2
            print(f"Setting V[{x}] to V[{x}] ^ V[{y}]")
        elif self.opcode & 0xF00F == 0x8004:
            self.V[x] += self.V[y]
            if self.V[x] > 255:
                self.V[0xF] = 1
            else:
                self.V[0xF] = 0
            self.pc += 2
            print(f"Adding V[{y}] to V[{x}]")
        elif self.opcode & 0xF00F == 0x8005:
            if self.V[x] > self.V[y]:
                self.V[0xF] = 1
            else:
                self.V[0xF] = 0
            self.V[x] -= self.V[y]
            self.pc += 2
            print(f"Subtracting V[{y}] from V[{x}]")
        elif self.opcode & 0xF00F == 0x8006:
            self.V[0xF] = self.V[x] & 0x1
            self.V[x] >>= 1
            self.pc += 2
            print(f"Setting V[{x}] to V[{x}] >> 1")
        elif self.opcode & 0xF00F == 0x8007:
            if self.V[y] > self.V[x]:
                self.V[0xF] = 1
            else:
                self.V[0xF] = 0
            self.V[x] = self.V[y] - self.V[x]
            self.pc += 2
            print(f"Setting V[{x}] to V[{y}] - V[{x}]")
        elif self.opcode & 0xF00F == 0x800E:
            self.V[0xF] = self.V[x] >> 7
            self.V[x] <<= 1
            self.pc += 2
            print(f"Setting V[{x}] to V[{x}] << 1")
        elif self.opcode & 0xF00F == 0x9000:
            if self.V[x] != self.V[y]:
                self.pc += 4
            else:
                self.pc += 2
            print(f"Skipping next instruction if V[{x}] != V[{y}]")
        elif self.opcode & 0xF000 == 0xA000:
            self.I = nnn
            self.pc += 2
            print(f"Setting I to {nnn}")
        elif self.opcode & 0xF000 == 0xB000:
            self.pc = nnn + self.V[0]
            print(f"Jumping to address {nnn} + V[0]")
        elif self.opcode & 0xF000 == 0xC000:
            self.V[x] = random.randint(0, 255) & nn
            self.pc += 2
            print(f"Setting V[{x}] to random number & {nn}")
        elif self.opcode & 0xF000 == 0xD000:
            self.V[0xF] = 0
            for row in range(n):
                sprite = self.memory[self.I + row]
                for col in range(8):
                    if sprite & (0x80 >> col) != 0:
                        if self.display[self.V[y] + row][self.V[x] + col] == 1:
                            self.V[0xF] = 1
                        self.display[self.V[y] + row][self.V[x] + col] ^= 1
            self.pc += 2
            print(f"Drawing a sprite at (V[{x}], V[{y}]) with height {n}")
        elif self.opcode & 0xF0FF == 0xE09E:
            if self.keyboard[self.V[x]] == 1:
                self.pc += 4
            else:
                self.pc += 2
            print(f"Skipping next instruction if key V[{x}] is pressed")
        elif self.opcode & 0xF0FF == 0xE0A1:
            if self.keyboard[self.V[x]] == 0:
                self.pc += 4
            else:
                self.pc += 2
            print(f"Skipping next instruction if key V[{x}] is not pressed")
        elif self.opcode & 0xF0FF == 0xF007:
            self.V[x] = self.delay_timer
            self.pc += 2
        elif self.opcode & 0xF0FF == 0xF00A:
            self.waiting_for_keypress = True
            self.key_register = x
            self.pc += 2
            print(f"Waiting for keypress and storing in V[{x}]")
        elif self.opcode & 0xF0FF == 0xF015:
            self.delay_timer = self.V[x]
            self.pc += 2
            print(f"Setting delay timer to V[{x}]")
        elif self.opcode & 0xF0FF == 0xF018:
            self.sound_timer = self.V[x]
            self.pc += 2
            print(f"Setting sound timer to V[{x}]")
        elif self.opcode & 0xF0FF == 0xF01E:
            self.I += self.V[x]
            self.pc += 2
            print(f"Adding V[{x}] to I")
        elif self.opcode & 0xF0FF == 0xF029:
            self.I = self.V[x] * 5
            self.pc += 2
            print(f"Setting I to the location of the sprite for digit V[{x}]")
        elif self.opcode & 0xF0FF == 0xF033:
            self.memory[self.I] = self.V[x] // 100
            self.memory[self.I + 1] = (self.V[x] // 10) % 10
            self.memory[self.I + 2] = self.V[x] % 10
            self.pc += 2
            print(f"Storing BCD representation of V[{x}] in memory")
        elif self.opcode & 0xF0FF == 0xF055:
            for i in range(x + 1):
                self.memory[self.I + i] = self.V[i]
            self.pc += 2
            print(f"Storing V[0] to V[{x}] in memory starting at address I")
        elif self.opcode & 0xF0FF == 0xF065:
            for i in range(x + 1):
                self.V[i] = self.memory[self.I + i]
            self.pc += 2
            print(f"Reading V[0] to V[{x}] from memory starting at address I")
        else:
            raise ValueError(f"Unknown opcode: {self.opcode}")

    def update_timers(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
            if self.sound_timer == 0:
                print("BEEP!")
