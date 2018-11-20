#version 450

#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

layout (location = 0) in vec3 inPos;

layout (set=0, binding=0) uniform View {
    mat4 mvp;
} view;


void main() 
{
    gl_Position = view.mvp * vec4(inPos, 1.0);
}
