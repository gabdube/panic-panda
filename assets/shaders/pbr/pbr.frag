#version 450

#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

#define PI 3.1415926535897932384626433832795
#define PI_2 (2.0*3.1415926535897932384626433832795)
#define INV_PI 1.0/PI
#define INV_LOG2 1.4426950408889634073599246810019
#define DefaultGamma 2.4

layout (location = 0) in vec3 inPos;
layout (location = 1) in vec3 inNormal;
layout (location = 2) in vec4 inTangent;
layout (location = 3) in vec2 inUv;

layout (location = 0) out vec4 outFragColor;

layout (set=0, binding=0) uniform Render {
    vec4 baseColorFactor;
    vec4 emissiveFactor;
    vec4 factors;                    // r: roughness / g: metallic / b: IBL brightness / a: unused
    vec4 envSphericalHarmonics[9];
    mat4 envTransform;
} render;

layout (set=1, binding=1) uniform sampler2DArray textureMaps;

struct PBR {
    vec3 normal;
    vec3 view;
    vec3 albedo;
    float roughness;
    vec3 specular;
    float ao;
};

const int diffuseIndex = 0;
const int metallicRoughnessIndex = 1;
const int normalIndex = 2;
const int aoIndex = 3;
const int emissiveIndex = 4;

//
// colorSpace.glsl BEGIN
//

float linearrgb_to_srgb1(const in float c, const in float gamma)
{
    float v = 0.0;
    if(c < 0.0031308) {
        if ( c > 0.0)
            v = c * 12.92;
    } else {
        v = 1.055 * pow(c, 1.0/ gamma) - 0.055;
    }
    return v;
}


vec4 linearTosRGB(const in vec4 col_from, const in float gamma)
{
    vec4 col_to;
    col_to.r = linearrgb_to_srgb1(col_from.r, gamma);
    col_to.g = linearrgb_to_srgb1(col_from.g, gamma);
    col_to.b = linearrgb_to_srgb1(col_from.b, gamma);
    col_to.a = col_from.a;
    return col_to;
}

vec3 linearTosRGB(const in vec3 col_from, const in float gamma)
{
    vec3 col_to;
    col_to.r = linearrgb_to_srgb1(col_from.r, gamma);
    col_to.g = linearrgb_to_srgb1(col_from.g, gamma);
    col_to.b = linearrgb_to_srgb1(col_from.b, gamma);
    return col_to;
}

float sRGBToLinear(const in float c, const in float gamma)
{
    float v = 0.0;
    if ( c < 0.04045 ) {
        if ( c >= 0.0 )
            v = c * ( 1.0 / 12.92 );
    } else {
        v = pow( ( c + 0.055 ) * ( 1.0 / 1.055 ), gamma );
    }
    return v;
}

vec4 sRGBToLinear(const in vec4 col_from, const in float gamma)
{
    vec4 col_to;
    col_to.r = sRGBToLinear(col_from.r, gamma);
    col_to.g = sRGBToLinear(col_from.g, gamma);
    col_to.b = sRGBToLinear(col_from.b, gamma);
    col_to.a = col_from.a;
    return col_to;
}

vec3 sRGBToLinear(const in vec3 col_from, const in float gamma)
{
    vec3 col_to;
    col_to.r = sRGBToLinear(col_from.r, gamma);
    col_to.g = sRGBToLinear(col_from.g, gamma);
    col_to.b = sRGBToLinear(col_from.b, gamma);
    return col_to;
}


//
// colorSpace.glsl END
//

//
// UE4 PBR begin
//

vec3 sphericalHarmonics(const vec3 sph[9], const in vec3 normal)
{
    float x = normal.x;
    float y = normal.y;
    float z = normal.z;

    vec3 result = (
        sph[0] +

        sph[1] * y +
        sph[2] * z +
        sph[3] * x +

        sph[4] * y * x +
        sph[5] * y * z +
        sph[6] * (3.0 * z * z - 1.0) +
        sph[7] * (z * x) +
        sph[8] * (x*x - y*y)
    );

    return max(result, vec3(0.0));
}

mat3 getEnvironmentTransform( mat4 transform ) {
    vec3 x = vec3(transform[0][0], transform[1][0], transform[2][0]);
    vec3 y = vec3(transform[0][1], transform[1][1], transform[2][1]);
    vec3 z = vec3(transform[0][2], transform[1][2], transform[2][2]);
    mat3 m = mat3(x,y,z);
    return m;
}

vec3 computeIBL(const in PBR pbr)
{
    float brightness = render.factors.b;
    mat3 environmentTransform = getEnvironmentTransform(render.envTransform);

    vec4 h[9] = render.envSphericalHarmonics;
    vec3 sph[9] = vec3[9](h[0].xyz, h[1].xyz, h[2].xyz, h[3].xyz, h[4].xyz, h[5].xyz, h[6].xyz, h[7].xyz, h[8].xyz);
    vec3 H = sphericalHarmonics(sph, environmentTransform * pbr.normal);

    vec3 color = brightness * pbr.albedo * pbr.ao * H;
    
    /*color += approximateSpecularIBL(specular,
                                    roughness,
                                    normal,
                                    view);*/

    return color;
}

//
// UE4 PBR end
//

vec3 computeNormalFromTangentSpaceNormalMap(const in vec4 tangent, const in vec3 normal, const in vec3 texnormal)
{
    vec3 tang = normalize(tangent.xyz);
    vec3 B = tangent.w * cross(normal, tang);
    vec3 outnormal = texnormal.x*tang + texnormal.y*B + texnormal.z*normal;
    return normalize(outnormal);
}

vec3 textureNormal(const in vec3 rgb) {
    vec3 n = normalize((rgb-vec3(0.5)));
    return n;
}

void main(void) {

    const vec3 dielectricColor = vec3(0.04);
    const float minRoughness = 1.e-4;

    // Fragment inputs
    vec3 normal = normalize(inNormal);
    vec3 eye = normalize(inPos);
    vec4 tangent = inTangent;
    vec2 uv = inUv.xy;

    // Uniforms inputs
    vec3 baseColorFactor = render.baseColorFactor.rgb,
         emissiveFactor = render.emissiveFactor.rgb;
    float roughnessFactor = render.factors.r,
          metallicFactor = render.factors.g;

    // Shaders locals
    vec4 albedoSource, result;
    vec3 albedo, albedoReduced, normalTexel, realNormal, specular, emissive, resultIBL;
    float roughness, ao, metallic;
    PBR pbr;
    
    // Diffuse
    albedoSource = texture(textureMaps, vec3(uv, diffuseIndex), 0.0);
    albedoSource.a *= render.baseColorFactor.a;
    albedo = sRGBToLinear( albedoSource.rgb, DefaultGamma ) * render.baseColorFactor.rgb;

    // Normals
    normalTexel = texture(textureMaps, vec3(uv, normalIndex), 0.0).rgb;
    realNormal = textureNormal( normalTexel );
    normal = computeNormalFromTangentSpaceNormalMap( tangent, normal, realNormal );
    
    // Roughness
    roughness = texture(textureMaps, vec3(uv, metallicRoughnessIndex), 0.0).g * roughnessFactor;
    roughness = max( minRoughness , roughness );

    // Metallic
    metallic = texture(textureMaps, vec3(uv, metallicRoughnessIndex), 0.0).b * metallicFactor;
    albedoReduced = albedo * (1.0 - metallic);
    specular = mix(dielectricColor, albedo, metallic);
    albedo = albedoReduced;

    // Ambient occlusion (FIX: should be included in the metallicRoughness map r channel, not in a separate layer)
    ao = texture(textureMaps, vec3(uv, aoIndex), 0.0).r;

    // PBR
    pbr.normal = normal;
    pbr.view = -eye;
    pbr.albedo = albedo;
    pbr.roughness = roughness;
    pbr.specular = specular;
    pbr.ao = ao;
    resultIBL = computeIBL(pbr);

    // Emissive
    emissive = texture(textureMaps, vec3(uv, emissiveIndex), 0.0).rgb * render.factors.b;
    resultIBL = resultIBL + emissive;

    // End result
    result = vec4(resultIBL, albedoSource.a);
    outFragColor = linearTosRGB(result, DefaultGamma);
}
