#version 450

#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

precision highp float;

layout (location = 0) in vec3 inPos;
layout (location = 1) in mat3 inTangent;

layout (location = 0) out vec4 outFragColor;

vec3 getNormal()
{
    vec3 n = normalize(inTangent[2].xyz);
    return n;
}

void main()
{
    vec3 n = getNormal();
    outFragColor = vec4(n, 1.0);
}
