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

uniform float fineDistance;  // distance from the camera when LOD is at its finest
uniform float coarseDistance;  // distance from the camera when LOD is at its coarsest
//uniform float coarsness;  // FOR DEBUGGING
uniform vec4 cameraWorldPosition;
uniform mat4 cameraToClipMatrix;
uniform mat4 worldToCameraMatrix;
uniform mat4 modelToWorldMatrix;

void main()
{
    // FOR DEBUGGING: disable this section
    float distance_to_camera = length(cameraWorldPosition - vec4(position, 0.0));
    float coarsness = 0.0;  // how coarse is this vertex
    if (distance_to_camera <= fineDistance)
    {
        coarsness = 0.0;
    }
    else if (distance_to_camera >= coarseDistance)
    {
        coarsness = 1.0;
    }
    else
    {
        coarsness = (distance_to_camera - fineDistance) / (coarsness - fineDistance);
    }

    vec4 world_position = modelToWorldMatrix * vec4(position, 1.0);
    vec4 transition_position = world_position + (vec4(positionTransitionVector, 0.0) * coarsness);
    gl_Position = cameraToClipMatrix * worldToCameraMatrix * transition_position;

    vec4 normal_in_world = normalize(modelToWorldMatrix * vec4(normal, 0.0) + (vec4(normalTransitionVector, 0.0) * coarsness));

    float cosAngIncidence = dot(normal_in_world, dirToLight);
    cosAngIncidence = clamp(cosAngIncidence, 0, 1);

    // float mult = ((position[1])/20.0);
    float mult = 1.0;
    interpColor = ((diffuseColor * lightIntensity * cosAngIncidence) +
        (diffuseColor * ambientIntensity)) * vec4(mult,mult,mult,1.0);
}
