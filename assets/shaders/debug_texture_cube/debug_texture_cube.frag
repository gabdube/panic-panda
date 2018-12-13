#version 450

#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

layout (location = 0) in vec3 inPos;
layout (location = 1) in mat3 inTbn;

layout (location = 0) out vec4 outColor;

layout (set=0, binding=0) uniform samplerCube cubeTexture;



void main() 
{
    float normalScale = 1.0;
    mat3 tbn = inTbn;
    vec3 n = normalize(tbn[2].xyz);

    vec3 diffuse = texture(cubeTexture, n).rgb;
    outColor = vec4(diffuse, 1.0);
}
