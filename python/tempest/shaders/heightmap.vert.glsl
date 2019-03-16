#version 410

// Input vertex data, different for all executions of this shader.
layout(location = 0) in vec3 vertex_position;
layout(location = 1) in vec2 vertex_uv;

// Output data ; will be interpolated for each fragment.
out vec2 uv;

void main()
{
    // Output position of the vertex in clip space
    gl_Position = vec4(vertex_position,1);

    // UV of the vertex. No special space for this one.
    uv = vertex_uv;
}
