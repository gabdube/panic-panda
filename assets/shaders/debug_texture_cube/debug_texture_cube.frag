#version 450

#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

layout (location = 0) in vec2 inUv;

layout (location = 0) out vec4 outColor;

layout (set=0, binding=0) uniform samplerCube cubeTexture;

layout (set=0, binding=2) uniform DebugParam {
    vec4 lod;
} params;

vec3 RGBMToRGB( const in vec4 rgba )
{
    const float maxRange = 8.0;
    return rgba.rgb * maxRange * rgba.a;
}

void main() 
{
    const float PI = 3.141592653589793238462643383;
    float lod = params.lod.x;

    vec3 cubmapTexCoords;
    cubmapTexCoords.x = -sin(inUv.x * PI * 2.0) * sin(inUv.y * PI);
    cubmapTexCoords.y = -cos(inUv.y * PI);
    cubmapTexCoords.z = -cos(inUv.x * PI * 2.0) * sin(inUv.y * PI);

    vec4 color = textureLod(cubeTexture, cubmapTexCoords, lod);
    vec3 rgbColor = RGBMToRGB(color);

    outColor = vec4(rgbColor, color.a);
}
