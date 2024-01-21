import ctypes
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pygame
import os


class Chip8Graphics:
    def __init__(self, width=640, height=320, rom_file=""):
        self.rom_file = os.path.basename(rom_file)
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_SWAP_CONTROL, 1)
        self.screen = pygame.display.set_mode(
            (width, height), pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE
        )
        glClearColor(0.44, 0.53, 0.0, 1.0)
        self.init_viewport(width, height)
        pygame.display.set_caption(f"CHIP-8 - {self.rom_file}")
        self.shader_program = self.compile_shader_program()
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        self.setup_vertex_buffer()
        self.window_width = width
        self.window_height = height
        self.display_changed = False

    def init_viewport(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)

    def load_shader_code(self, filename):
        with open(filename, "r") as file:
            return file.read()

    def guess_shader_type(self, shader_code):
        vertex_keywords = ["gl_Position", "layout(location)"]
        fragment_keywords = ["gl_FragColor", "out vec4"]
        geometry_keywords = [
            "gl_in",
            "layout(points) in",
            "layout(lines) in",
            "layout(triangles) in",
        ]
        tessellation_control_keywords = ["gl_PatchVerticesIn", "layout(vertices"]
        tessellation_evaluation_keywords = ["gl_TessCoord"]
        compute_keywords = [
            "layout(local_size_x",
            "layout(local_size_y",
            "layout(local_size_z",
        ]
        if any(keyword in shader_code for keyword in vertex_keywords):
            return GL_VERTEX_SHADER
        elif any(keyword in shader_code for keyword in fragment_keywords):
            return GL_FRAGMENT_SHADER
        elif any(keyword in shader_code for keyword in geometry_keywords):
            return GL_GEOMETRY_SHADER
        elif any(keyword in shader_code for keyword in tessellation_control_keywords):
            return GL_TESS_CONTROL_SHADER
        elif any(
            keyword in shader_code for keyword in tessellation_evaluation_keywords
        ):
            return GL_TESS_EVALUATION_SHADER
        elif any(keyword in shader_code for keyword in compute_keywords):
            return GL_COMPUTE_SHADER
        else:
            return None

    def compile_shader_program(self):
        shader_program = None
        shaders = []
        shader_files = os.listdir("shaders")
        for filename in shader_files:
            shader_code = self.load_shader_code(os.path.join("shaders", filename))
            shader_type = self.guess_shader_type(shader_code)

            if shader_type is not None:
                shader = compileShader(shader_code, shader_type)
                shaders.append(shader)

        if shaders:
            shader_program = compileProgram(*shaders)

        return shader_program

    def setup_vertex_buffer(self):
        self.vertices = np.array(
            [
                -1.0,
                1.0,
                0.0,
                0.0,  # Top-left
                1.0,
                1.0,
                1.0,
                0.0,  # Top-right
                1.0,
                -1.0,
                1.0,
                1.0,  # Bottom-right
                -1.0,
                -1.0,
                0.0,
                1.0,  # Bottom-left
            ],
            dtype=np.float32,
        )
        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(
            GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW
        )
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))
        glEnableVertexAttribArray(1)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def update_display(self, new_display):
        self.display_data = (
            np.repeat(new_display[:, :, np.newaxis], 3, axis=2).astype(np.uint8) * 255
        )
        self.display_changed = True

    def draw_graphics(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(self.shader_program)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        if self.display_changed:
            glTexImage2D(
                GL_TEXTURE_2D,
                0,
                GL_RGB,
                64,
                32,
                0,
                GL_RGB,
                GL_UNSIGNED_BYTE,
                self.display_data,
            )
            self.display_changed = False

        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindTexture(GL_TEXTURE_2D, 0)
        pygame.display.flip()

    def handle_resize(self, new_width, new_height):
        glViewport(0, 0, new_width, new_height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, new_width, new_height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        self.window_width = new_width
        self.window_height = new_height
