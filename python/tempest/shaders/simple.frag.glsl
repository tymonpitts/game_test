#version 410

smooth in vec3 interpColor;

out vec3 color;

void main(){
    color = interpColor;
}
