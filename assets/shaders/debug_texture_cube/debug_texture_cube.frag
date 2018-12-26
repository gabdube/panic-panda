#version 450

#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

layout (location = 0) in vec2 inUv;

layout (location = 0) out vec4 outColor;

layout (set=0, binding=0) uniform samplerCube cubeTexture;

layout (set=0, binding=2) uniform DebugParam {
    vec4 lod;
} params;

vec3 LUVToRGB( const in vec4 vLogLuv )
{
    const mat3 LUVInverse = mat3( 6.0013,    -2.700,   -1.7995,
                              -1.332,    3.1029,   -5.7720,
                              0.3007,    -1.088,    5.6268 );

    float Le = vLogLuv.z * 255.0 + vLogLuv.w;
    vec3 Xp_Y_XYZp;
    Xp_Y_XYZp.y = exp2((Le - 127.0) / 2.0);
    Xp_Y_XYZp.z = Xp_Y_XYZp.y / vLogLuv.y;
    Xp_Y_XYZp.x = vLogLuv.x * Xp_Y_XYZp.z;
    vec3 vRGB = LUVInverse * Xp_Y_XYZp;
    return max(vRGB, 0.0);
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
    vec3 rgbColor = LUVToRGB(color);

    outColor = vec4(rgbColor, color.a);
}
