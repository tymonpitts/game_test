#version 410

layout (location = 0) in vec2 clip_position_offset;
layout (location = 1) in vec2 texture_coordinates;

out vec2 vertex_texture_coordinates;

uniform vec3 world_position = vec3(0.0);
uniform mat4 camera_to_clip_matrix;
uniform mat4 world_to_camera_matrix = mat4(1.0);

void main()
{
    vec4 point_position = camera_to_clip_matrix * world_to_camera_matrix * vec4(world_position, 1.0);
    if (point_position.z < -1)
    {
        // bail out if the point is behind the camera, otherwise the
        // text will still be drawn on the screen
        gl_Position = point_position;
        return;
    }
    // apply perspective divide now
    point_position.xy /= point_position.w;
    gl_Position = vec4(point_position.xy + clip_position_offset, 0.0, 1.0);

    vertex_texture_coordinates = texture_coordinates;
}
