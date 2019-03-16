#version 410

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;

smooth out vec4 interpColor;

uniform vec4 lightIntensity;
uniform vec4 ambientIntensity;
uniform vec4 diffuseColor;
uniform vec4 dirToLight;

uniform mat4 cameraToClipMatrix;
uniform mat4 worldToCameraMatrix;
uniform mat4 modelToWorldMatrix;

void main()
{
    mat4 model_to_camera = worldToCameraMatrix * modelToWorldMatrix;
    gl_Position = cameraToClipMatrix * model_to_camera * vec4(position, 1.0);

    vec4 normal_in_world = normalize(modelToWorldMatrix * vec4(normal, 0.0));

    float cosAngIncidence = dot(normal_in_world, dirToLight);
    cosAngIncidence = clamp(cosAngIncidence, 0, 1);

    // float mult = ((position[1])/20.0);
    float mult = 1.0;
    interpColor = ((diffuseColor * lightIntensity * cosAngIncidence) +
        (diffuseColor * ambientIntensity)) * vec4(mult,mult,mult,1.0);

}
