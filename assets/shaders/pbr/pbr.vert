#version 450

#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

layout (location = 0) in vec3 inPos;
layout (location = 1) in vec3 inNormal;
layout (location = 2) in vec2 inUv;

layout (location = 0) out vec3 outPos;
layout (location = 1) out vec2 outUv;
layout (location = 2) out vec3 outNormal;

layout (set=2, binding=0) uniform Timer {
    float runtime;
};

layout (set=3, binding=0) uniform AnimationChannels {
    int translationInterpolation;
    int rotationInterpolation;
    int scaleInterpolation;
} ch;

layout (set=1, binding=0) uniform View {
    mat4 mvp;
    mat4 model;
    mat4 normal;
} view;


void main(void) 
{
    vec4 pos = view.model * vec4(inPos, 1.0);
    outPos = pos.xyz;

    outNormal = normalize(vec3(view.model * vec4(inNormal.xyz, 0.0)));

    outUv = inUv;

    gl_Position = view.mvp * vec4(inPos, 1.0);
}
