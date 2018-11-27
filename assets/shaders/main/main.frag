#version 450

#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

layout (location = 0) in vec3 inPos;
layout (location = 1) in mat3 inTbn;

layout (location = 0) out vec4 outColor;

// Render data that won't change much (if at all) during a scene draw
layout (set=0, binding=0) uniform RenderStatic {
    vec4 lightColor;
    vec4 lightDirection;
    vec4 cameraPos;
} rstatic;

struct PBRInfo
{
    float NdotL;                  // cos angle between normal and light direction
    float NdotV;                  // cos angle between normal and view direction
    float NdotH;                  // cos angle between normal and half vector
    float LdotH;                  // cos angle between light direction and half vector
    float VdotH;                  // cos angle between view direction and half vector
    float perceptualRoughness;    // roughness value, as authored by the model creator (input to shader)
    float metalness;              // metallic value at the surface
    vec3 reflectance0;            // full reflectance color (normal incidence angle)
    vec3 reflectance90;           // reflectance color at grazing angle
    float alphaRoughness;         // roughness mapped to a more linear change in the roughness (proposed by [2])
    vec3 diffuseColor;            // color contribution from diffuse lighting
    vec3 specularColor;           // color contribution from specular lighting
};


// Other constants
const float M_PI = 3.141592653589793;
const float minRoughness = 0.04;
const vec3 F0 = vec3(0.04);
const vec3 F1 = vec3(0.96);

vec4 baseColorValues() {
    return vec4(0.5, 0.5, 0.5, 1.0);
}

vec3 metallicRoughnessValues() {
    float perceptualRoughness = 0.5;
    float alphaRoughness = perceptualRoughness * perceptualRoughness;
    float metallic = 0.5;
    
    return vec3(perceptualRoughness, alphaRoughness, metallic);
}

vec3 getNormal() {
    float normalScale = 1.0;
    mat3 tbn = inTbn;
    //vec3 n = texture(textureMaps, vec3(v_uv, NORMALS_INDEX) ).rgb;
    //n = normalize(tbn * ((2.0 * n - 1.0) * vec3(normalScale, normalScale, 1.0)));

    vec3 n = normalize(tbn[2].xyz);

    return n;
}

vec3 specularReflection(PBRInfo pbrInputs)
{
    return pbrInputs.reflectance0 + (pbrInputs.reflectance90 - pbrInputs.reflectance0) * pow(clamp(1.0 - pbrInputs.VdotH, 0.0, 1.0), 5.0);
}

float microfacetDistribution(PBRInfo pbrInputs)
{
    float roughnessSq = pbrInputs.alphaRoughness * pbrInputs.alphaRoughness;
    float f = (pbrInputs.NdotH * roughnessSq - pbrInputs.NdotH) * pbrInputs.NdotH + 1.0;
    return roughnessSq / (M_PI * f * f);
}

float geometricOcclusion(PBRInfo pbrInputs)
{
    float NdotL = pbrInputs.NdotL;
    float NdotV = pbrInputs.NdotV;
    float r = pbrInputs.alphaRoughness;

    float attenuationL = 2.0 * NdotL / (NdotL + sqrt(r * r + (1.0 - r * r) * (NdotL * NdotL)));
    float attenuationV = 2.0 * NdotV / (NdotV + sqrt(r * r + (1.0 - r * r) * (NdotV * NdotV)));
    return attenuationL * attenuationV;
}

vec3 diffuse(PBRInfo pbrInputs)
{
    return pbrInputs.diffuseColor / M_PI;
}

void main() {
    // Unpack uniforms
    vec3 lightColor = rstatic.lightColor.rgb;
    vec3 lightDirection = rstatic.lightDirection.xyz;
    vec3 cameraPos = rstatic.cameraPos.xyz;

    // Color
    vec4 baseColor = baseColorValues();
    
    // MetallicRoughness
    vec3 mrValues = metallicRoughnessValues();
    float perceptualRoughness = mrValues.r;
    float alphaRoughness = mrValues.g;
    float metallic = mrValues.b;

    // PBR compute
    vec3 diffuseColor = (baseColor.rgb * F1) * (1.0 - metallic);
    vec3 specularColor = mix(F0, baseColor.rgb, metallic);

    float reflectance = max(max(specularColor.r, specularColor.g), specularColor.b);
    float reflectance90 = clamp(reflectance * 25.0, 0.0, 1.0);
    vec3 specularEnvironmentR0 = specularColor.rgb;
    vec3 specularEnvironmentR90 = vec3(1.0, 1.0, 1.0) * reflectance90;

    vec3 n = getNormal();                           // normal at surface point
    vec3 v = normalize(cameraPos - inPos);     // Vector from surface point to camera
    vec3 l = normalize(lightDirection);             // Vector from surface point to light
    vec3 h = normalize(l+v);                        // Half vector between both l and v
    vec3 reflection = -normalize(reflect(v, n));

    float NdotL = clamp(dot(n, l), 0.001, 1.0);
    float NdotV = clamp(abs(dot(n, v)), 0.001, 1.0);
    float NdotH = clamp(dot(n, h), 0.0, 1.0);
    float LdotH = clamp(dot(l, h), 0.0, 1.0);
    float VdotH = clamp(dot(v, h), 0.0, 1.0);

    PBRInfo pbrInputs = PBRInfo(
        NdotL,
        NdotV,
        NdotH,
        LdotH,
        VdotH,
        perceptualRoughness,
        metallic,
        specularEnvironmentR0,
        specularEnvironmentR90,
        alphaRoughness,
        diffuseColor,
        specularColor
    );

    // Calculate the shading terms for the microfacet specular shading model
    vec3 F = specularReflection(pbrInputs);
    float G = geometricOcclusion(pbrInputs);
    float D = microfacetDistribution(pbrInputs);

    // Calculation of analytical lighting contribution
    vec3 diffuseContrib = (1.0 - F) * diffuse(pbrInputs);
    vec3 specContrib = F * G * D / (4.0 * NdotL * NdotV);

    // Obtain final intensity as reflectance (BRDF) scaled by the energy of the light (cosine law)
    vec3 color = NdotL * lightColor * (diffuseContrib + specContrib);

    outColor = vec4(pow(color,vec3(1.0/2.2)), baseColor.a);
}
