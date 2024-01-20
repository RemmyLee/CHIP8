import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GL.shaders import compileProgram, compileShader
import ctypes


class Chip8Graphics:
    def __init__(self, width=640, height=320):
        # Initialize Pygame and the OpenGL context
        pygame.init()
        pygame.display.set_mode((width, height), pygame.DOUBLEBUF | pygame.OPENGL)
        glClearColor(0.44, 0.53, 0.0, 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, 640, 320, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        pygame.display.set_caption("CHIP-8 Emulator")

        # Compile the shader program
        self.shader_program = self.compile_shader_program()

        # Create a texture ID and set parameters
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        # Setup the vertex buffer
        self.setup_vertex_buffer()

        # Store window dimensions
        self.window_width = width
        self.window_height = height

    def compile_shader_program(self):
        # Vertex shader code
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
        # Fragment shader code
        fragment_shader_code = """
        #version 330 core
        out vec4 FragColor;
        in vec2 TexCoord;
        uniform sampler2D screenTexture;
        const float offset = 1.0 / 300.0; // Offset for the blur effect, adjust as needed

        vec4 blur(vec2 texCoords) {
            vec4 result = vec4(0.0);
            float kernel[5] = float[](0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);
            for (int x = -2; x <= 2; x++) {
                for (int y = -2; y <= 2; y++) {
                    vec2 shift = vec2(float(x) * offset, float(y) * offset);
                    result += texture(screenTexture, texCoords + shift) * kernel[abs(x)] * kernel[abs(y)];
                }
            }
            return result;
        }

        void main() {
            vec4 color = texture(screenTexture, TexCoord);
            vec4 blurredColor = blur(TexCoord);
            color += blurredColor * blurredColor.a; // Using alpha channel to control the intensity of the glow
            float scanline = sin(TexCoord.y * 3.14 * 32.0) * 0.05;
            color.rgb += vec3(scanline);
            color.rgb = pow(color.rgb, vec3(0.8)); // Apply a gamma correction to simulate the brightness of a CRT

            FragColor = color;
        }
        """
        # Compile shaders
        vertex_shader = compileShader(vertex_shader_code, GL_VERTEX_SHADER)
        fragment_shader = compileShader(fragment_shader_code, GL_FRAGMENT_SHADER)
        return compileProgram(vertex_shader, fragment_shader)

    def setup_vertex_buffer(self):
        # Define the quad vertices with the corresponding texture coordinates
        # The vertices are defined for the full window size
        self.vertices = np.array(
            [
                # Positions   # Texture Coords
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

        # Generate a buffer ID and bind the VBO
        self.VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(
            GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW
        )

        # Enable the vertex attribute arrays
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))
        glEnableVertexAttribArray(1)

        # Unbind the VBO
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def draw_graphics(self, display):
        glClear(GL_COLOR_BUFFER_BIT)

        # Use the shader program
        glUseProgram(self.shader_program)

        # Bind the texture
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        # Update the texture with the current CHIP-8 display data
        display_data = np.array(display, dtype=np.uint8) * 255
        display_data = np.repeat(
            display_data[:, :, np.newaxis], 3, axis=2
        )  # Convert to RGB
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGB, 64, 32, 0, GL_RGB, GL_UNSIGNED_BYTE, display_data
        )

        # Bind the VBO
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)

        # Draw the quad
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

        # Unbind the VBO and texture
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindTexture(GL_TEXTURE_2D, 0)

        # Swap the buffers
        pygame.display.flip()


# Usage example
# graphics = Chip8Graphics()
# while running:
#     # Your game loop here
#     graphics.draw_graphics(cpu.display)  # Pass the CHIP-8 display data to the draw function
