import random
import time


class Chip8CPU:
    def __init__(self):
        self.memory = [0] * 4096
        self.V = [0] * 16
        self.I = 0
        self.pc = 0x200
        self.stack = [0] * 16
        self.sp = 0
        self.delay_timer = 0
        self.sound_timer = 0
        self.display = [[0 for _ in range(64)] for _ in range(32)]
        self.waiting_for_keypress = False
        self.key_register = None
        self.opcode = 0
        self.last_timer_update = time.time()
        self.load_fontset()

    def reset(self):
        self.memory = [0] * 4096
        self.V = [0] * 16
        self.I = 0
        self.pc = 0x200
        self.stack = [0] * 16
        self.sp = 0
        self.delay_timer = 0
        self.sound_timer = 0
        self.display = [[0 for _ in range(64)] for _ in range(32)]
        self.waiting_for_keypress = False
        self.key_register = None
        self.opcode = 0
        self.last_timer_update = time.time()
        self.load_fontset()

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
            self.memory[0x50 + i] = fontset[i]

    def load_game(self, filename):
        with open(filename, "rb") as game:
            game_data = game.read()
            for i, byte in enumerate(game_data):
                self.memory[0x200 + i] = byte

    def emulate_cycle(self):
        if not self.waiting_for_keypress:
            self.fetch_opcode()
            self.execute_opcode()
            if self.pc >= 0xFFE:
                self.pc = 0x200
                return
        current_time = time.time()
        if current_time - self.last_timer_update >= 1 / 60:
            self.update_timers()
            self.last_timer_update = current_time

    def fetch_opcode(self):
        self.opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]

    def execute_opcode(self):
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        n = self.opcode & 0x000F
        nn = self.opcode & 0x00FF
        nnn = self.opcode & 0x0FFF

        if self.opcode == 0x00E0:  # 00E0 - CLS
            """Clear the display."""
            self.display = [[0 for _ in range(64)] for _ in range(32)]
            self.pc += 2

        elif self.opcode == 0x00EE:  # 00EE - RET
            """Return from a subroutine."""
            self.sp -= 1
            self.pc = self.stack[self.sp]
            self.pc += 2

        elif self.opcode & 0xF000 == 0x0000:  # 0nnn - SYS addr
            """Jump to a machine code routine at nnn. This instruction is only used on the old computers on which Chip-8 was originally implemented. It is ignored by modern interpreters."""
            self.pc += 2

        elif self.opcode & 0xF000 == 0x1000:  # 1nnn - JP addr
            """Jump to location nnn."""
            self.pc = nnn

        elif self.opcode & 0xF000 == 0x2000:  # 2nnn - CALL addr
            """Call subroutine at nnn."""
            self.stack[self.sp] = self.pc
            self.sp += 1
            self.pc = nnn

        elif self.opcode & 0xF000 == 0x3000:  # 3xnn - SE Vx, byte
            """Skip next instruction if Vx = nn."""
            if self.V[x] == nn:
                self.pc += 4
            else:
                self.pc += 2

        elif self.opcode & 0xF000 == 0x4000:  # 4xnn - SNE Vx, byte
            """Skip next instruction if Vx != nn."""
            if self.V[x] != nn:
                self.pc += 4
            else:
                self.pc += 2

        elif self.opcode & 0xF00F == 0x5000:  # 5xy0 - SE Vx, Vy
            """Skip next instruction if Vx = Vy."""
            if self.V[x] == self.V[y]:
                self.pc += 4
            else:
                self.pc += 2

        elif self.opcode & 0xF000 == 0x6000:  # 6xnn  - LD Vx, byte
            """Set Vx = nn."""
            self.V[x] = nn
            self.pc += 2

        elif self.opcode & 0xF000 == 0x7000:  # 7xnn - ADD Vx, byte
            """Set Vx = Vx + nn."""
            self.V[x] = (self.V[x] + nn) & 0xFF
            self.pc += 2

        elif self.opcode & 0xF00F == 0x8000:  # 8xy0 - LD Vx, Vy
            """Set Vx = Vy."""
            self.V[x] = self.V[y]
            self.pc += 2

        elif self.opcode & 0xF00F == 0x8001:  # 8xy1 - OR Vx, Vy
            """Set Vx = Vx OR Vy."""
            self.V[x] |= self.V[y]
            self.pc += 2

        elif self.opcode & 0xF00F == 0x8002:  # 8xy2 - AND Vx, Vy
            """Set Vx = Vx AND Vy."""
            self.V[x] &= self.V[y]
            self.pc += 2

        elif self.opcode & 0xF00F == 0x8003:  # 8xy3 - XOR Vx, Vy
            """Set Vx = Vx XOR Vy."""
            self.V[x] ^= self.V[y]
            self.pc += 2

        elif self.opcode & 0xF00F == 0x8004:  # 8xy4 - ADD Vx, Vy
            """Set Vx = Vx + Vy, set VF = carry."""
            sum_val = self.V[x] + self.V[y]
            self.V[x] = sum_val & 0xFF
            self.V[0xF] = 1 if sum_val > 255 else 0
            self.pc += 2

        elif self.opcode & 0xF00F == 0x8005:  # 8xy5 - SUB Vx, Vy
            """Set Vx = Vx - Vy, set VF = NOT borrow."""
            vx_value = self.V[x]
            vy_value = self.V[y]
            self.V[x] = (vx_value - vy_value) & 0xFF
            self.V[0xF] = 1 if vx_value >= vy_value else 0
            self.pc += 2

        elif self.opcode & 0xF00F == 0x8006:  # 8xy6 - SHR Vx {, Vy}
            """Set Vx = Vx SHR 1."""
            vx_value = self.V[x]
            self.V[x] = (self.V[x] >> 1) & 0xFF
            self.V[0xF] = vx_value & 0x1
            self.pc += 2

        elif self.opcode & 0xF00F == 0x8007:  # 8xy7 - SUBN Vx, Vy
            """Set Vx = Vy - Vx, set VF = NOT borrow."""
            self.V[x] = (self.V[y] - self.V[x]) & 0xFF
            self.V[0xF] = 1 if self.V[y] >= self.V[x] else 0
            self.pc += 2

        elif self.opcode & 0xF00F == 0x800E:  # 8xyE - SHL Vx {, Vy}
            """Set Vx = Vx SHL 1."""
            vx_value = self.V[x]
            self.V[x] = (self.V[x] << 1) & 0xFF
            self.V[0xF] = (vx_value & 0x80) >> 7
            self.pc += 2

        elif self.opcode & 0xF00F == 0x9000:  # 9xy0 - SNE Vx, Vy
            """Skip next instruction if Vx != Vy."""
            if self.V[x] != self.V[y]:
                self.pc += 4
            else:
                self.pc += 2

        elif self.opcode & 0xF000 == 0xA000:  # Annn - LD I, addr
            """Set I = nnn."""
            self.I = nnn
            self.pc += 2

        elif self.opcode & 0xF000 == 0xB000:  # Bnnn - JP V0, addr
            """Jump to location nnn + V0."""
            self.pc = nnn + self.V[0]

        elif self.opcode & 0xF000 == 0xC000:  # Cxnn - RND Vx, byte
            """Set Vx = random byte AND nn."""
            self.V[x] = random.randint(0, 255) & nn
            self.pc += 2

        elif self.opcode & 0xF000 == 0xD000:  # Dxyn - DRW Vx, Vy, nibble
            """Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision."""
            x = self.V[x] % 64
            y = self.V[y] % 32
            height = n
            self.V[0xF] = 0
            for yline in range(height):
                pixel = self.memory[self.I + yline]
                for xline in range(8):
                    if (pixel & (0x80 >> xline)) != 0:
                        dx = x + xline
                        dy = y + yline
                        if 0 <= dx < 64 and 0 <= dy < 32:
                            if self.display[dy][dx] == 1:
                                self.V[0xF] = 1
                            self.display[dy][dx] ^= 1
            self.pc += 2

        elif self.opcode & 0xF0FF == 0xE09E:  # Ex9E - SKP Vx
            """Skip next instruction if key with the value of Vx is pressed."""
            if self.keyboard[self.V[x]] == 1:
                self.pc += 4
            else:
                self.pc += 2

        elif self.opcode & 0xF0FF == 0xE0A1:  # ExA1 - SKNP Vx
            """Skip next instruction if key with the value of Vx is not pressed."""
            if self.keyboard[self.V[x]] == 0:
                self.pc += 4
            else:
                self.pc += 2

        elif self.opcode & 0xF0FF == 0xF007:  # Fx07 - LD Vx, DT
            """Set Vx = delay timer value."""
            self.V[x] = self.delay_timer
            self.pc += 2

        elif self.opcode & 0xF0FF == 0xF00A:  # Fx0A - LD Vx, K
            """Wait for a key press, store the value of the key in Vx."""
            self.waiting_for_keypress = True
            self.key_register = x
            self.pc += 2

        elif self.opcode & 0xF0FF == 0xF015:  # Fx15 - LD DT, Vx
            """Set delay timer = Vx."""
            self.delay_timer = self.V[x]
            self.pc += 2

        elif self.opcode & 0xF0FF == 0xF018:  # Fx18 - LD ST, Vx
            """Set sound timer = Vx."""
            self.sound_timer = self.V[x]
            self.pc += 2

        elif self.opcode & 0xF0FF == 0xF01E:  # Fx1E - ADD I, Vx
            """Set I = I + Vx."""
            self.I = (self.I + self.V[x]) & 0xFFF
            self.pc += 2

        elif self.opcode & 0xF0FF == 0xF029:  # Fx29 - LD F, Vx
            """Set I = location of sprite for digit Vx."""
            self.I = 0x50 + (self.V[x] * 5)
            self.pc += 2

        elif self.opcode & 0xF0FF == 0xF033:  # Fx33 - LD B, Vx
            """Store BCD representation of Vx in memory locations I, I+1, and I+2."""
            self.memory[self.I] = self.V[x] // 100
            self.memory[self.I + 1] = (self.V[x] // 10) % 10
            self.memory[self.I + 2] = self.V[x] % 10
            self.pc += 2

        elif self.opcode & 0xF0FF == 0xF055:  # Fx55 - LD [I], Vx
            """Store registers V0 through Vx in memory starting at location I."""
            for i in range(x + 1):
                self.memory[self.I + i] = self.V[i]
            self.I += x + 1
            self.pc += 2

        elif self.opcode & 0xF0FF == 0xF065:  # Fx65 - LD Vx, [I]
            """Read registers V0 through Vx from memory starting at location I."""
            for i in range(x + 1):
                self.V[i] = self.memory[self.I + i]
            self.I += x + 1
            self.pc += 2
        else:
            raise ValueError(f"Unknown opcode: {self.opcode}")

    def update_timers(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
            if self.sound_timer == 0:
                pass
