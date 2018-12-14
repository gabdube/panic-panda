#version 450

#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

layout (location = 0) in vec2 inUv;

layout (location = 0) out vec4 outColor;

layout (set=0, binding=0) uniform samplerCube cubeTexture;


void main() 
{
    const float PI = 3.141592653589793238462643383;

    vec3 cubmapTexCoords;
    cubmapTexCoords.x = -sin(inUv.x * PI * 2.0) * sin(inUv.y * PI);
    cubmapTexCoords.y = -cos(inUv.y * PI);
    cubmapTexCoords.z = -cos(inUv.x * PI * 2.0) * sin(inUv.y * PI);

    outColor = texture(cubeTexture, cubmapTexCoords);
}
