#version 410

in vec2 vertex_texture_coordinates;

uniform sampler2D glyph_texture;
uniform vec4 color;

out vec4 final_color;

void main()
{
    vec4 sampled = vec4(1.0, 1.0, 1.0, texture(glyph_texture, vertex_texture_coordinates).r);
    final_color = color * sampled;
}
