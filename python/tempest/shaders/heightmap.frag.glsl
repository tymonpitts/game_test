#version 410

// Interpolated values from the vertex shaders
in vec2 uv;

// Ouput data
out vec3 color;

// Values that stay constant for the whole mesh.
uniform sampler2D textureSampler;

void main()
{
    // Output color = color of the texture at the specified UV
    color = texture(textureSampler, uv).rgb;
}
