#version 450

#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

precision highp float;

layout (location = 0) in vec3 inPos;
layout (location = 1) in vec2 inUv;
layout (location = 2) in mat3 inTangent;

layout (location = 0) out vec4 outFragColor;

layout (set=1, binding=1) uniform sampler2D normalMaps;

layout (set=0, binding=0) uniform Debug {
    ivec4 debug1;  // Normal Map / Normals / 
};


vec3 getNormal()
{
    mat3 tbn = inTangent;
    vec3 n = texture(normalMaps, inUv).rgb;
    n = normalize(tbn * ((2.0 * n - 1.0) * vec3(-1.0, 1.0, 1.0)));

    //vec3 n = normalize(tbn[2].xyz);

    return n;
}

void main()
{
    vec3 n = getNormal();

    vec3 color;
    if (debug1[0] == 1){
        vec3 normalUv = texture(normalMaps, inUv).rgb;
        color = normalUv;
    }
    else if (debug1[1] == 1)
        color = n;
    else
        color = vec3(0.0);

    outFragColor = vec4(color, 1.0);
}
