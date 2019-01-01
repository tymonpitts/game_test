#version 330

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;

smooth out vec3 interpColor;

uniform mat4 cameraToClipMatrix;
uniform mat4 worldToCameraMatrix;
uniform mat4 modelToWorldMatrix;

void main()
{
    gl_Position = cameraToClipMatrix * worldToCameraMatrix * modelToWorldMatrix * vec4(position, 1.0);
    interpColor = normal;
}
