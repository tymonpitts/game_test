#version 330

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;
layout(location = 2) in vec3 positionTransitionVector;
layout(location = 3) in vec3 normalTransitionVector;

smooth out vec4 interpColor;

uniform vec4 lightIntensity;
uniform vec4 ambientIntensity;
uniform vec4 diffuseColor;
uniform vec4 dirToLight;

uniform float transitionEndDistance;  // distance from the camera when LOD transition from coarse to fine is finished
uniform float transitionRange;  // distance from transitionEndDistance to start LOD transition from coarse to fine
uniform vec4 cameraWorldPosition;
uniform mat4 cameraToClipMatrix;
uniform mat4 worldToCameraMatrix;
uniform mat4 modelToWorldMatrix;

void main()
{
    float distance_to_camera = length(cameraWorldPosition - vec4(position, 0.0));
    float transition = clamp(((distance_to_camera - transitionEndDistance) / transitionRange), 0, 1);
    vec4 world_position = modelToWorldMatrix * vec4(position, 1.0);
    vec4 transition_position = world_position + (vec4(positionTransitionVector, 0.0) * transition);
    gl_Position = cameraToClipMatrix * worldToCameraMatrix * transition_position;

    vec4 normal_in_world = normalize(modelToWorldMatrix * vec4(normal, 0.0) + (vec4(normalTransitionVector, 0.0) * transition));

    float cosAngIncidence = dot(normal_in_world, dirToLight);
    cosAngIncidence = clamp(cosAngIncidence, 0, 1);

    // float mult = ((position[1])/20.0);
    float mult = 1.0;
    interpColor = ((diffuseColor * lightIntensity * cosAngIncidence) +
        (diffuseColor * ambientIntensity)) * vec4(mult,mult,mult,1.0);
}
