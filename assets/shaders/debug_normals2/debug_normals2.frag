#version 450

#extension GL_ARB_separate_shader_objects : enable
#extension GL_ARB_shading_language_420pack : enable

precision highp float;

layout (location = 0) in vec3 inPos;
layout (location = 1) in vec2 inUv;
layout (location = 2) in vec3 inNormal;

layout (location = 0) out vec4 outFragColor;

layout (set=1, binding=1) uniform sampler2D normalMaps;

layout (set=0, binding=0) uniform Debug {
    ivec4 debug1;  // Normal Map / Normals / 
};


vec3 getNormal()
{
    vec3 pos_dx = dFdx(inPos);
    vec3 pos_dy = dFdy(inPos);
    vec3 tex_dx = dFdx(vec3(inUv, 0.0));
    vec3 tex_dy = dFdy(vec3(inUv, 0.0));
    vec3 t = (tex_dy.t * pos_dx - tex_dx.t * pos_dy) / (tex_dx.s * tex_dy.t - tex_dy.s * tex_dx.t);
    vec3 ng = normalize(inNormal);
    
    t = normalize(t - ng * dot(ng, t));
    vec3 b = normalize(cross(ng, t));
    mat3 tbn = mat3(t, b, ng);

    vec3 n = texture(normalMaps, inUv).rgb;
    n = normalize(tbn * ((2.0 * n - 1.0) * vec3(1.0, 1.0, 1.0)));

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
