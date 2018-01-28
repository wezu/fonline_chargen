//GLSL
//Based on MattiasCRT shader by Mattias, License Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
//https://www.shadertoy.com/view/Ms23DR
#version 130
uniform sampler2D color_tex;
uniform float osg_FrameTime;

in vec2 base_uv;

vec2 curve(vec2 uv)
    {
    uv = (uv - 0.5) * 2.0;
    uv *= 1.1;
    uv.x *= 1.0 + pow((abs(uv.y) / 16.0), 2.0);
    uv.y *= 1.0 + pow((abs(uv.x) / 9.0), 2.0);
    uv  = (uv / 2.0) + 0.5;
    uv =  uv *0.92 + 0.04;
    return uv;
    }

void main()
    {
    vec2 res=textureSize(color_tex, 0).xy;
    vec2 pixel = vec2(1.0, 1.0)/res;
    vec2 uv = curve( base_uv );
    vec3 base_color = texture( color_tex, uv ).xyz;
    vec3 crt_color;
    float x =  sin(0.3*osg_FrameTime+uv.y*21.0)*sin(0.7*osg_FrameTime+uv.y*29.0)*sin(0.3+0.33*osg_FrameTime+uv.y*31.0)*0.00057;

    vec3 chroma_distort = vec3(-3.75, 2.5, 7.5) *(0.2+abs(distance(uv, base_uv))*20.0);
    crt_color.r = texture(color_tex, uv +uv*pixel* chroma_distort.x).r;
    crt_color.g = texture(color_tex, uv +uv*pixel* chroma_distort.y).g;
    crt_color.b = texture(color_tex, uv +uv*pixel* chroma_distort.z).b;

    crt_color = clamp(crt_color*0.6+0.4*crt_color*crt_color,0.0,1.0);

    float vig = (0.0 + 16.0*uv.x*uv.y*(1.0-uv.x)*(1.0-uv.y));
    crt_color *= vec3(pow(vig,0.3));
    crt_color*=(2.66, 2.94, 2.66);

    float scans = clamp( 0.35+0.35*sin(3.5*osg_FrameTime+uv.y*res.y*1.5), 0.0, 1.0);

    float s = pow(scans,1.7);
    crt_color = crt_color*vec3( 0.4+0.7*s) ;
    crt_color *= 1.0+0.05*sin(110.0*osg_FrameTime);
    crt_color*=1.0-0.65*vec3(clamp((mod(gl_FragCoord.x, 2.0)-1.0)*2.0,0.0,1.0));

    gl_FragData[0] = vec4(mix(crt_color,base_color,0.4),1.0);
    }

