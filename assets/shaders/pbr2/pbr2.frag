#version 450

#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

precision highp float;

layout (location = 0) in vec3 inPos;
layout (location = 1) in vec2 inUv;
layout (location = 2) in vec3 inNormal;

layout (location = 0) out vec4 outFragColor;

layout (set=0, binding=1) uniform sampler2D brdfLUT;
layout (set=0, binding=2) uniform samplerCube envSpecular;
layout (set=0, binding=3) uniform samplerCube envIrradiance;
layout (set=1, binding=1) uniform sampler2DArray maps;

layout (set=0, binding=0) uniform Render {
    vec4 lightDirection;
    vec4 lightColor;
    vec4 camera;
    vec4 envLod;   // 0: Min LOD / 1: Max LOD
    vec4 factors;  // 0: Base color / 1: Emissive / 2: Exposure / 3: Gamma
    ivec4 debug;
} render;

const float M_PI = 3.141592653589793;
const int DIFFUSE_INDEX = 0;
const int METALLIC_ROUGHNESS_INDEX = 1;
const int NORMALS_INDEX = 2;
const int AO_INDEX = 3;
const int EMISSIVE_INDEX = 4;

struct PBRInfo
{
    float NdotL;
    float NdotV;
    float NdotH;
    float LdotH;
    float VdotH;
    float perceptualRoughness;
    float metalness;
    vec3 reflectance0;
    vec3 reflectance90;
    float alphaRoughness;
    vec3 diffuseColor;
    vec3 specularColor;
};

vec3 Uncharted2Tonemap(vec3 color)
{
	float A = 0.15;
	float B = 0.50;
	float C = 0.10;
	float D = 0.20;
	float E = 0.02;
	float F = 0.30;
	float W = 11.2;
	return ((color*(A*color+C*B)+D*E)/(color*(A*color+B)+D*F))-E/F;
}

vec4 tonemap(vec4 color)
{
    float exposure = render.factors[2];
    float gamma = render.factors[3];

	vec3 outcol = Uncharted2Tonemap(color.rgb * exposure);
	outcol = outcol * (1.0f / Uncharted2Tonemap(vec3(11.2f)));	
	return vec4(pow(outcol, vec3(1.0f / gamma)), 1.0);
}

vec4 SRGBtoLINEAR(vec4 srgbIn)
{
    vec3 bLess = step(vec3(0.04045),srgbIn.xyz);
    vec3 linOut = mix( srgbIn.xyz/vec3(12.92), pow((srgbIn.xyz+vec3(0.055))/vec3(1.055),vec3(2.4)), bLess );
    return vec4(linOut,srgbIn.w);
}

vec4 getBaseColor() {
    vec4 color = texture(maps, vec3(inUv, DIFFUSE_INDEX)) * render.factors[0];
    return SRGBtoLINEAR(color);
}

vec3 getMetallicRoughness() {
    vec4 mrSample = texture(maps, vec3(inUv, METALLIC_ROUGHNESS_INDEX));
    float perceptualRoughness, alphaRoughness, metallic;

    perceptualRoughness = clamp(mrSample.g, 0.04, 1.0);
    alphaRoughness = perceptualRoughness * perceptualRoughness;
    metallic = clamp(mrSample.b, 0.0, 1.0);
    
    return vec3(perceptualRoughness, alphaRoughness, metallic);
}

vec3 getNormals() {
    vec3 tangentNormal = texture(maps, vec3(inUv, NORMALS_INDEX) ).xyz * 2.0 - 1.0;

	vec3 q1 = dFdx(inPos);
	vec3 q2 = dFdy(inPos);
	vec2 st1 = dFdx(inUv);
	vec2 st2 = dFdy(inUv);

	vec3 N = normalize(inNormal);
	vec3 T = normalize(q1 * st2.t - q2 * st1.t);
	vec3 B = -normalize(cross(N, T));
	mat3 TBN = mat3(T, B, N);

	return normalize(TBN * tangentNormal);
}

vec3 specularReflection(PBRInfo pbrInputs)
{
    return pbrInputs.reflectance0 + (pbrInputs.reflectance90 - pbrInputs.reflectance0) * pow(clamp(1.0 - pbrInputs.VdotH, 0.0, 1.0), 5.0);
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

float microfacetDistribution(PBRInfo pbrInputs)
{
    float roughnessSq = pbrInputs.alphaRoughness * pbrInputs.alphaRoughness;
    float f = (pbrInputs.NdotH * roughnessSq - pbrInputs.NdotH) * pbrInputs.NdotH + 1.0;
    return roughnessSq / (M_PI * f * f);
}

vec3 diffuse(PBRInfo pbrInputs)
{
    return pbrInputs.diffuseColor / M_PI;
}

vec3 getIBLContribution(PBRInfo pbrInputs, vec3 n, vec3 reflection)
{
    float mipCount = render.envLod[1]; 
    float lod = (pbrInputs.perceptualRoughness * mipCount);

    vec3 brdf = texture(brdfLUT, vec2(pbrInputs.NdotV, 1.0 - pbrInputs.perceptualRoughness)).rgb;

    vec3 diffuseLight = SRGBtoLINEAR(tonemap(texture(envIrradiance, n))).rgb;
    vec3 diffuse = diffuseLight * pbrInputs.diffuseColor;

    vec3 specularLight = SRGBtoLINEAR(tonemap(texture(envSpecular, reflection, lod))).rgb;
    vec3 specular = specularLight * (pbrInputs.specularColor * brdf.x + brdf.y);

    return diffuse + specular;
}

void main() 
{
    vec4 baseColor = getBaseColor();
    
    vec3 mr = getMetallicRoughness();
    float perceptualRoughness = mr[0];
    float alphaRoughness = mr[1];
    float metallic = mr[2];

    const vec3 f0 = vec3(0.04);
    const vec3 f1 = vec3(1.0) - f0;
    vec3 diffuseColor = (baseColor.rgb * f1) * (1.0 - metallic);
    vec3 specularColor = mix(f0, baseColor.rgb, metallic);

    float reflectance = max(max(specularColor.r, specularColor.g), specularColor.b);
    float reflectance90 = clamp(reflectance * 25.0, 0.0, 1.0);
    vec3 specularEnvironmentR0 = specularColor.rgb;
    vec3 specularEnvironmentR90 = vec3(1.0, 1.0, 1.0) * reflectance90;

    vec3 n = getNormals();
    vec3 v = normalize(render.camera.xyz - inPos);
    vec3 l = normalize(render.lightDirection.xyz);
    vec3 h = normalize(l+v);
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

    vec3 F = specularReflection(pbrInputs);
    float G = geometricOcclusion(pbrInputs);
    float D = microfacetDistribution(pbrInputs);

    vec3 diffuseContrib = (1.0 - F) * diffuse(pbrInputs);
    vec3 specContrib = F * G * D / (4.0 * NdotL * NdotV);
    vec3 color = NdotL * render.lightColor.rgb * (diffuseContrib + specContrib);

    vec3 colorFinal = color + getIBLContribution(pbrInputs, n, reflection);

    float ao = texture(maps, vec3(inUv, AO_INDEX)).r;
    const float occlusion_strength = 1.0;
    colorFinal = mix(colorFinal, colorFinal * ao, occlusion_strength);

    vec3 emissive = SRGBtoLINEAR(texture(maps, vec3(inUv, EMISSIVE_INDEX))).rgb * render.factors[1];
    colorFinal += emissive;

    int debug = render.debug[0];
    vec4 outColor;

    if (debug == 0)
        outColor = vec4(pow(colorFinal,vec3(1.0/2.2)), baseColor.a);
    else if (debug == 1)
        outColor = baseColor;
    else if (debug == 2)
        outColor = vec4(diffuseColor, 1.0);
    else if (debug == 3)
        outColor = vec4(specularColor, 1.0);
    else if (debug == 4) 
        outColor = vec4(perceptualRoughness, perceptualRoughness, perceptualRoughness, 1.0);
    else if (debug == 5) 
        outColor = vec4(metallic, metallic, metallic, 1.0);
    else if (debug == 6)
        outColor = vec4(n, 1.0);
    else if (debug == 7)
        outColor = vec4(F, 1.0);
    else if (debug == 8)
        outColor = vec4(G, G, G, 1.0);
    else if (debug == 9)
        outColor = vec4(D, D, D, 1.0);
    else if (debug == 10)
        outColor = vec4(color, 1.0);

    outFragColor = outColor;
}
