#version 410

layout(location = 0) in vec3 position;

smooth out vec4 interpColor;

uniform vec4 color;

uniform mat4 cameraToClipMatrix;
uniform mat4 worldToCameraMatrix;
uniform mat4 modelToWorldMatrix;

void main()
{
    gl_PointSize = 10.0;
    mat4 model_to_camera = worldToCameraMatrix * modelToWorldMatrix;
    gl_Position = cameraToClipMatrix * model_to_camera * vec4(position, 1.0);
    interpColor = color;
}
