#version 450

#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

layout (location = 0) in vec3 inPos;
layout (location = 1) in vec3 inNormal;
layout (location = 2) in vec4 inTangent;

layout (location = 0) out vec3 outPos;
layout (location = 1) out mat3 outTbn;

layout (set=2, binding=0) uniform View {
    mat4 mvp;
    mat4 normal;
    mat4 model;
} view;


void main() 
{
    vec4 pos = view.model * vec4(inPos, 1.0);
  
    vec3 normalW = normalize(vec3(view.normal * vec4(inNormal.xyz, 0.0)));
    vec3 tangentW = normalize(vec3(view.model * vec4(inTangent.xyz, 0.0)));
    vec3 bitangentW = cross(normalW, tangentW) * inTangent.w;

    outPos = vec3(pos.xyz) / pos.w;
    outTbn = mat3(tangentW, bitangentW, normalW);

    gl_Position = view.mvp * vec4(inPos, 1.0);
}
