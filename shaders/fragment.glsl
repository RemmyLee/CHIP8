#version 330 core
out vec4 FragColor;
in vec2 TexCoord;
uniform sampler2D screenTexture;
const int blurSize = 2;
const float offset = 1.0 / 350.0;
vec4 blur(vec2 texCoords)
{
    vec4 result = vec4(0.0);
    float kernel[9] = float[](0.0625, 0.125, 0.25, 0.25, 0.25, 0.25, 0.125, 0.0625, 0.03125);
    for (int x = -blurSize; x <= blurSize; x++)
    {
        for (int y = -blurSize; y <= blurSize; y++)
        {
            vec2 shift = vec2(float(x) * offset, float(y) * offset);
            result += texture(screenTexture, texCoords + shift) * kernel[abs(x)] * kernel[abs(y)];
        }
    }
    return result;
}

void main()
{
    vec4 color = texture(screenTexture, TexCoord);
    vec4 blurredColor = blur(TexCoord);
    vec3 greenColor = vec3(0.4, 1.0, 0.0);
    if (color.r > 0.5)
    {
        color.rgb = greenColor;
    }
    color += blurredColor * 1;
    float scanline = sin(TexCoord.y * 3.14 * 160.0) * 0.05;
    color.rgb += vec3(scanline);
    color.rgb = pow(color.rgb, vec3(0.8));
    FragColor = color;
}