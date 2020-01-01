#version 410

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;

smooth out vec4 vertex_color;

uniform vec4 diffuse_color = vec4(0.5, 0.5, 0.5, 1.0);
uniform vec3 light_intensity = vec3(0.8, 0.8, 0.8);
uniform vec3 ambient_intensity = vec3(0.2, 0.2, 0.2);
uniform vec3 direction_to_light = normalize(vec3(0.1, 1.0, 0.5));

uniform mat4 camera_to_clip_matrix;
uniform mat4 world_to_camera_matrix = mat4(1.0);
uniform mat4 model_to_world_matrix = mat4(1.0);

void main()
{
    mat4 model_to_camera = world_to_camera_matrix * model_to_world_matrix;
    gl_Position = camera_to_clip_matrix * model_to_camera * vec4(position, 1.0);

    vec4 normal_in_world = normalize(model_to_world_matrix * vec4(normal, 0.0));

    float cos_angle_incidence = dot(normal_in_world, -vec4(direction_to_light, 0.0));
    cos_angle_incidence = clamp(cos_angle_incidence, 0, 1);

    // float mult = ((position[1])/20.0);
    float mult = 1.0;
    vertex_color = ((diffuse_color * vec4(light_intensity, 1.0) * cos_angle_incidence) +
        (diffuse_color * vec4(ambient_intensity, 1.0))) * vec4(mult,mult,mult,1.0);

}
