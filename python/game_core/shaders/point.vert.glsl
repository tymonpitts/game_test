#version 410

layout(location = 0) in vec3 position;

uniform vec4 color = vec4(0.0, 0.0, 0.0, 1.0);
uniform int size = 10;
uniform mat4 camera_to_clip_matrix;
uniform mat4 world_to_camera_matrix = mat4(1.0);
uniform mat4 model_to_world_matrix = mat4(1.0);

smooth out vec4 vertex_color;

void main()
{
    gl_PointSize = size;
    gl_Position = camera_to_clip_matrix * world_to_camera_matrix * model_to_world_matrix * vec4(position, 1.0);
    vertex_color = color;
}
