import pygame
import logging
import random
from OpenGL.GL import *
from OpenGL.GLUT import *
import tkinter as tk
from threading import Thread
import time

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Chip8:
    def __init__(self, filename):
        pygame.init()
        self.window_width, self.window_height = 640, 320
        pygame.display.set_mode(
            (self.window_width, self.window_height), pygame.DOUBLEBUF | pygame.OPENGL
        )
        glClearColor(0.44, 0.53, 0.0, 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, 64, 32, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        pygame.display.set_caption(f"CHIP-8 Emulator: {filename}")

        self.memory = [0] * 4096
        self.V = [0] * 16
        self.I = 0
        self.pc = 0x200
        self.stack = [0] * 16
        self.sp = -1
        self.delay_timer = 0
        self.sound_timer = 0
        self.key = [0] * 16
        self.display = [[0 for _ in range(64)] for _ in range(32)]
        self.waiting_for_keypress = False
        self.key_register = None
        self.opcode = 0
        self.last_timer_update = time.time()
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
        }
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
        self.opcode_patterns = {
            0x00E0: "CLS",
            0x00EE: "RET",
            0x1000: "JP {nnn}",
            0x2000: "CALL {nnn}",
            0x3000: "SE V{x}, {kk}",
            0x4000: "SNE V{x}, {kk}",
            0x5000: "SE V{x}, V{y}",
            0x6000: "LD V{x}, {kk}",
            0x7000: "ADD V{x}, {kk}",
            0x8000: "LD V{x}, V{y}",
            0x8001: "OR V{x}, V{y}",
            0x8002: "AND V{x}, V{y}",
            0x8003: "XOR V{x}, V{y}",
            0x8004: "ADD V{x}, V{y}",
            0x8005: "SUB V{x}, V{y}",
            0x8006: "SHR V{x}",
            0x8007: "SUBN V{x}, V{y}",
            0x800E: "SHL V{x}",
            0x9000: "SNE V{x}, V{y}",
            0xA000: "LD I, {nnn}",
            0xB000: "JP V0, {nnn}",
            0xC000: "RND V{x}, {kk}",
            0xD000: "DRW V{x}, V{y}, {n}",
            0xE09E: "SKP V{x}",
            0xE0A1: "SKNP V{x}",
            0xF007: "LD V{x}, DT",
            0xF00A: "LD V{x}, K",
            0xF015: "LD DT, V{x}",
            0xF018: "LD ST, V{x}",
            0xF01E: "ADD I, V{x}",
            0xF029: "LD F, V{x}",
            0xF033: "LD B, V{x}",
            0xF055: "LD [I], V{x}",
            0xF065: "LD V{x}, [I]",
        }
        self.load_fontset()
        self.load_game(filename)

    def setup_hex_viewer(self):
        self.hex_viewer_thread = Thread(target=self.run_hex_viewer, daemon=True)
        self.hex_viewer_thread.start()

    def run_hex_viewer(self):
        self.hex_viewer_root = tk.Tk()
        self.hex_viewer_root.title("Hex Viewer")
        self.hex_viewer_text = tk.Text(self.hex_viewer_root, font=("Courier", 10))
        self.hex_viewer_text.pack(expand=True, fill=tk.BOTH)
        self.update_hex_viewer()
        self.hex_viewer_root.mainloop()

    def update_hex_viewer(self):
        scroll_pos = self.hex_viewer_text.yview()
        self.hex_viewer_text.delete("1.0", tk.END)
        hex_dump = "\n".join(
            f"{i:04X}: " + " ".join(f"{byte:02X}" for byte in self.memory[i : i + 16])
            for i in range(0, len(self.memory), 16)
        )
        self.hex_viewer_text.insert("1.0", hex_dump)
        self.hex_viewer_text.yview_moveto(scroll_pos[0])
        self.hex_viewer_root.after(16, self.update_hex_viewer)

    def load_fontset(self):
        fontset = [
            0xF0,
            0x90,
            0x90,
            0x90,
            0xF0,
            0x20,
            0x60,
            0x20,
            0x20,
            0x70,
            0xF0,
            0x10,
            0xF0,
            0x80,
            0xF0,
            0xF0,
            0x10,
            0xF0,
            0x10,
            0xF0,
            0x90,
            0x90,
            0xF0,
            0x10,
            0x10,
            0xF0,
            0x80,
            0xF0,
            0x10,
            0xF0,
            0xF0,
            0x80,
            0xF0,
            0x90,
            0xF0,
            0xF0,
            0x10,
            0x20,
            0x40,
            0x40,
            0xF0,
            0x90,
            0xF0,
            0x90,
            0xF0,
            0xF0,
            0x90,
            0xF0,
            0x10,
            0xF0,
            0xF0,
            0x90,
            0xF0,
            0x90,
            0x90,
            0xE0,
            0x90,
            0xE0,
            0x90,
            0xE0,
            0xF0,
            0x80,
            0x80,
            0x80,
            0xF0,
            0xE0,
            0x90,
            0x90,
            0x90,
            0xE0,
            0xF0,
            0x80,
            0xF0,
            0x80,
            0xF0,
            0xF0,
            0x80,
            0xF0,
            0x80,
            0x80,
        ]
        for i in range(len(fontset)):
            self.memory[0x50 + i] = fontset[i]

    def get_opcode_description(self, opcode):
        nnn = opcode & 0x0FFF
        kk = opcode & 0x00FF
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        n = opcode & 0x000F
        for pattern, message in self.opcode_patterns.items():
            if (opcode & 0xF000) == (pattern & 0xF000):
                if pattern & 0x0F00:
                    if (opcode & 0x0F00) != (pattern & 0x0F00):
                        continue
                if pattern & 0x00F0:
                    if (opcode & 0x00F0) != (pattern & 0x00F0):
                        continue
                if pattern & 0x00FF:
                    if (opcode & 0x00FF) != (pattern & 0x00FF):
                        continue
                return message.format(nnn=nnn, kk=kk, x=x, y=y, n=n)
        return "Unknown opcode"

    def fetch_opcode(self):
        self.opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]

    def execute_opcode(self):
        self.opcode_table[self.opcode & 0xF000]()

    def opcode_0xxx(self):
        opcode = self.opcode & 0x00FF
        if opcode in self.opcode_table_0xxx:
            self.opcode_table_0xxx[opcode]()

    def opcode_00E0(self):
        self.display = [[0 for _ in range(64)] for _ in range(32)]
        self.pc += 2

    def opcode_00EE(self):
        self.sp -= 1
        self.pc = self.stack[self.sp]
        self.pc += 2

    def opcode_1xxx(self):
        nn = self.opcode & 0x0FFF
        self.pc = nn

    def opcode_2xxx(self):
        nn = self.opcode & 0x0FFF
        self.stack[self.sp] = self.pc
        self.sp += 1
        self.pc = nn

    def opcode_3xxx(self):
        x = (self.opcode & 0x0F00) >> 8
        nn = self.opcode & 0x00FF
        if self.V[x] == nn:
            self.pc += 4
        else:
            self.pc += 2

    def opcode_4xxx(self):
        x = (self.opcode & 0x0F00) >> 8
        nn = self.opcode & 0x00FF
        if self.V[x] != nn:
            self.pc += 4
        else:
            self.pc += 2

    def opcode_5xxx(self):
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        n = self.opcode & 0x000F
        if n != 0x0:
            raise ValueError(f"Invalid opcode: {hex(self.opcode)}")
        if self.V[x] == self.V[y]:
            self.pc += 4
        else:
            self.pc += 2

    def opcode_6xxx(self):
        x = (self.opcode & 0x0F00) >> 8
        nn = self.opcode & 0x00FF
        self.V[x] = nn
        self.pc += 2

    def opcode_7xxx(self):
        x = (self.opcode & 0x0F00) >> 8
        nn = self.opcode & 0x00FF
        self.V[x] = (self.V[x] + nn) & 0xFF
        self.pc += 2

    def opcode_8xxx(self):
        func = self.opcode_table_8xxx.get(self.opcode & 0x000F)
        if func:
            func()

    def opcode_8xy0(self):
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        self.V[x] = self.V[y]
        self.pc += 2

    def opcode_8xy1(self):
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        self.V[x] |= self.V[y]
        self.pc += 2

    def opcode_8xy2(self):
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        self.V[x] &= self.V[y]
        self.pc += 2

    def opcode_8xy3(self):
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        self.V[x] ^= self.V[y]
        self.V[0xF] = 0
        self.pc += 2

    def opcode_8xy4(self):
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        sum = self.V[x] + self.V[y]
        self.V[x] = sum & 0xFF
        self.V[0xF] = 1 if sum > 0xFF else 0
        self.pc += 2

    def opcode_8xy5(self):
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        self.V[0xF] = 1 if self.V[x] >= self.V[y] else 0
        self.V[x] = (self.V[x] - self.V[y]) & 0xFF
        self.pc += 2

    def opcode_8xy6(self):
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        self.V[0xF] = self.V[y] & 0x1
        self.V[x] = self.V[y] >> 1
        self.pc += 2

    def opcode_8xy7(self):
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        if self.V[y] >= self.V[x]:
            self.V[0xF] = 1
        else:
            self.V[0xF] = 0
        self.V[x] = (self.V[y] - self.V[x]) & 0xFF
        self.pc += 2

    def opcode_8xyE(self):
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        self.V[0xF] = (self.V[y] & 0x80) >> 7
        self.V[x] = (self.V[y] << 1) & 0xFF
        self.pc += 2

    def opcode_9xxx(self):
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        if self.V[x] != self.V[y]:
            self.pc += 4
        else:
            self.pc += 2

    def opcode_Axxx(self):
        self.I = self.opcode & 0x0FFF
        self.pc += 2

    def opcode_Bxxx(self):
        self.pc = self.V[0] + (self.opcode & 0x0FFF)

    def opcode_Cxxx(self):
        x = (self.opcode & 0x0F00) >> 8
        byte = self.opcode & 0x00FF
        self.V[x] = random.randint(0, 255) & byte
        self.pc += 2

    def opcode_Dxxx(self):
        x = self.V[(self.opcode & 0x0F00) >> 8] % 64
        y = self.V[(self.opcode & 0x00F0) >> 4] % 32
        height = self.opcode & 0x000F
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

    def opcode_Exxx(self):
        self.opcode_table_Exxx[self.opcode & 0x00FF]()

    def opcode_Ex9E(self):
        x = (self.opcode & 0x0F00) >> 8
        key = self.V[x]
        if self.key[key]:
            self.pc += 4
        else:
            self.pc += 2

    def opcode_ExA1(self):
        x = (self.opcode & 0x0F00) >> 8
        key = self.V[x]
        if not self.key[key]:
            self.pc += 4
        else:
            self.pc += 2

    def opcode_Fxxx(self):
        func = self.opcode_table_Fxxx.get(self.opcode & 0x00FF)
        if func:
            func()
        else:
            raise ValueError(f"Invalid opcode: {hex(self.opcode)}")

    def opcode_Fx07(self):
        x = (self.opcode & 0x0F00) >> 8
        self.V[x] = self.delay_timer
        self.pc += 2

    def opcode_Fx0A(self):
        x = (self.opcode & 0x0F00) >> 8
        key_pressed = False
        for i in range(16):
            if self.key[i]:
                self.V[x] = i
                key_pressed = True
                break
        if not key_pressed:
            self.waiting_for_keypress = True

    def opcode_Fx15(self):
        x = (self.opcode & 0x0F00) >> 8
        self.delay_timer = self.V[x]
        self.pc += 2

    def opcode_Fx18(self):
        x = (self.opcode & 0x0F00) >> 8
        self.sound_timer = self.V[x]
        self.pc += 2

    def opcode_Fx1E(self):
        x = (self.opcode & 0x0F00) >> 8
        self.I += self.V[x]
        self.pc += 2

    def opcode_Fx29(self):
        x = (self.opcode & 0x0F00) >> 8
        digit = self.V[x]
        self.I = 0x50 + (5 * digit)
        self.pc += 2

    def opcode_Fx33(self):
        x = (self.opcode & 0x0F00) >> 8
        self.memory[self.I] = self.V[x] // 100
        self.memory[self.I + 1] = (self.V[x] // 10) % 10
        self.memory[self.I + 2] = (self.V[x] % 100) % 10
        self.pc += 2

    def opcode_Fx55(self):
        x = (self.opcode & 0x0F00) >> 8
        for i in range(x + 1):
            self.memory[self.I + i] = self.V[i]
        self.pc += 2

    def opcode_Fx65(self):
        x = (self.opcode & 0x0F00) >> 8
        for i in range(x + 1):
            self.V[i] = self.memory[self.I + i]
        self.pc += 2

    def emulate_cycle(self):
        if not self.waiting_for_keypress:
            self.fetch_opcode()
            self.execute_opcode()
        else:
            if self.check_keys():
                self.waiting_for_keypress = False
        self.fetch_opcode()
        self.execute_opcode()
        current_time = time.time()
        if current_time - self.last_timer_update >= 1 / 60:
            self.update_timers()
            self.last_timer_update = current_time

    def update_timers(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
            if self.sound_timer == 1:
                print("BEEP!")

    def set_keys(self):
        keys = pygame.key.get_pressed()
        key_map = self.key_map
        for key, value in key_map.items():
            self.key[value] = 1 if keys[key] else 0

    def draw_graphics(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glColor3f(0.25, 0.32, 0.11)
        scaling_factor = 1
        glBegin(GL_QUADS)
        for x in range(64):
            for y in range(32):
                if self.display[y][x] == 1:
                    glVertex2f(x * scaling_factor, y * scaling_factor)
                    glVertex2f((x + 1) * scaling_factor, y * scaling_factor)
                    glVertex2f((x + 1) * scaling_factor, (y + 1) * scaling_factor)
                    glVertex2f(x * scaling_factor, (y + 1) * scaling_factor)
        glEnd()
        pygame.display.flip()

    def print_registers(self):
        logging.debug("Register state:")
        for i, v in enumerate(self.V):
            logging.info(f"V{i:X}: {v:02X}")
        logging.debug(f"I: {self.I:03X}")
        logging.debug(f"PC: {self.pc:03X}")
        logging.debug(f"SP: {self.sp:02X}")

    def load_game(self, filename):
        print("Loading game: " + filename)
        with open(filename, "rb") as game:
            game_data = game.read()
            print(len(game_data))
            print(f"Loading game into memory at address 0x200.")
            for i, byte in enumerate(game_data):
                self.memory[0x200 + i] = byte

    def main_loop(self):
        running = True
        self.setup_hex_viewer()
        while running:
            if self.key_register is not None:
                print(f"Key register: {hex(self.key_register)}")
            else:
                print("Key register: None")
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
            time.sleep(1 / 500)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python chip8.py [ROM file]")
        sys.exit(1)
    game_filename = sys.argv[1]
    chip8 = Chip8(game_filename)
    chip8.main_loop()
