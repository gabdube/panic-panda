#version 450

#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

layout (location = 0) in vec2 inUv;

layout (location = 0) out vec4 outFragColor;

layout (set=0, binding=1) uniform sampler2D color_texture;


void main() 
{
    outFragColor = texture(color_texture, inUv, 0.0);
}
