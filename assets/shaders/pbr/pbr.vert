#version 450

#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

layout (location = 0) in vec3 inPos;
layout (location = 1) in vec3 inNormal;
layout (location = 2) in vec2 inUv;
layout (location = 3) in vec4 inTangent;

layout (location = 0) out vec3 outPos;
layout (location = 1) out vec3 outNormal;
layout (location = 2) out vec4 outTangent;
layout (location = 3) out vec2 outUv;

layout (set=1, binding=0) uniform View {
    mat4 modelView;
    mat4 projection;
    mat3 modelViewNormal;
} view;


void main(void) {

    outPos = vec3(view.modelView * vec4(inPos, 1.0));
    outNormal = view.modelViewNormal * inNormal;
    outTangent = vec4(view.modelViewNormal * inTangent.xyz, inTangent.w);
    outUv = inUv;

    gl_Position = view.projection * view.modelView * vec4(inPos, 1.0);
}
