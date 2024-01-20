import ctypes
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GL.shaders import compileProgram, compileShader
import pygame


class Chip8Graphics:
    def __init__(self, width=640, height=320):
        pygame.init()
        pygame.display.set_mode(
            (width, height), pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE
        )
        glClearColor(0.44, 0.53, 0.0, 1.0)
        self.init_viewport(width, height)
        pygame.display.set_caption("CHIP-8 Emulator")
        self.shader_program = self.compile_shader_program()
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        self.setup_vertex_buffer()
        self.window_width = width
        self.window_height = height
        self.display_changed = False  # Flag to track if display has changed

    def init_viewport(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)

    def compile_shader_program(self):
        vertex_shader_code = """
        #version 330 core
        layout (location = 0) in vec2 aPos;
        layout (location = 1) in vec2 aTexCoord;

        out vec2 TexCoord;

        void main() {
            gl_Position = vec4(aPos.x, aPos.y, 0.0, 1.0);
            TexCoord = aTexCoord;
        }
        """

        fragment_shader_code = """
        #version 330 core
        out vec4 FragColor;
        in vec2 TexCoord;
        uniform sampler2D screenTexture;
        const int blurSize = 2;
        const float offset = 1.0 / 350.0;
        vec4 blur(vec2 texCoords) {
            vec4 result = vec4(0.0);
            float kernel[9] = float[](0.0625, 0.125, 0.25, 0.25, 0.25, 0.25, 0.125, 0.0625, 0.03125);
            for (int x = -blurSize; x <= blurSize; x++) {
                for (int y = -blurSize; y <= blurSize; y++) {
                    vec2 shift = vec2(float(x) * offset, float(y) * offset);
                    result += texture(screenTexture, texCoords + shift) * kernel[abs(x)] * kernel[abs(y)];
                }
            }
            return result;
        }

        void main() {
            vec4 color = texture(screenTexture, TexCoord);
            vec4 blurredColor = blur(TexCoord);
            vec3 greenColor = vec3(0.4, 1.0, 0.0); // RGB for green
            if (color.r > 0.5) {
                color.rgb = greenColor;
            }
            color += blurredColor * 0.8; // Adjust the multiplier to achieve the desired glow intensity
            float scanline = sin(TexCoord.y * 3.14 * 128.0) * 0.05;
            color.rgb += vec3(scanline);
            color.rgb = pow(color.rgb, vec3(0.8));
            FragColor = color;
        }
        """
        vertex_shader = compileShader(vertex_shader_code, GL_VERTEX_SHADER)
        fragment_shader = compileShader(fragment_shader_code, GL_FRAGMENT_SHADER)
        return compileProgram(vertex_shader, fragment_shader)

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
        self.window_width = new_width
        self.window_height = new_height
