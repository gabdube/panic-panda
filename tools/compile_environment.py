"""
This script process .hdr/.exr/.tif environment map files into a specular cubemap and a irradiance cubemap.
The images are then processed by the "compress_images" script and then (FINALLY), the generated .ktx files
are processed by "ktxmerge.py" to create two ktx cubemap.

TODO: just send one list of commands to docker instead of calling it a bajillion times

Dependencies:

* envtool [ https://github.com/cedricpinson/envtools ] it is assumed that the tool was installed with docker

Usage:

`python compile_environment.py --path PATH --input INPUT`
"""

from pathlib import Path
from os import getuid
import sys, subprocess, platform, math, re

argv = sys.argv

path_index = argv.index("--path")
path = Path(argv[path_index+1]).resolve()

input_index = argv.index("--input")
input_env = argv[input_index+1]
input_env_docker = "data/"+input_env

def process(args, text):
    global output 

    if text is not None:
        print(f"\nGenerating {text}")

    print(" ".join(args))

    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    process.communicate()
    
    if text is not None:
        print(f"Generated {text}\n")


# Prepare the shared space between docker and the host
out_path = path/"out"
out_path.mkdir(exist_ok=True)

spec_path = out_path/"spec"
spec_path.mkdir(exist_ok=True)

spec_face_path = spec_path/"faces"
spec_face_path.mkdir(exist_ok=True)

irr_face_path = out_path/"irr_faces"
irr_face_path.mkdir(exist_ok=True)

env_tool_args = ("docker", "run",  "-v", f"{path}:/data", "-t", "trigrou/envtools")

# 1. generate a .tif panorama from the input file
original_panorama = "data/out/original_panorama.tiff"
args = env_tool_args + ('oiiotool', '-v', input_env_docker, '--clamp:max=1040.0', '--clamp:min=0', '-o', original_panorama)
process(args, f"{original_panorama} from {input_env}")

# 2. generate a high quality cubemap
hres_cubemap = "data/out/highres_cubemap.tiff"
args = env_tool_args + ('envremap', '-p', 'rgss', '-n', '1024', '-o', 'cube', original_panorama, hres_cubemap)
process(args, f"{hres_cubemap} from {original_panorama}")

# 3. generate the specular cubemap mipmaps
generated_mipmaps = []
last_spec_cubemap = "data/out/highres_cubemap.tiff"
size, target_mip_size = 1024, 512
mipmap_count = int(math.log(size, 2))

for i in range(mipmap_count):
    size //= 2
    if size > target_mip_size:
        continue  # Skip the first mipmap until we reach target_mip_size

    spec_cubemap = f"data/out/spec/specular_cubemap_{i}.tiff"
    args = env_tool_args + ('envremap', '-p', 'rgss', '-n', str(size), '-i', 'cube', '-o', 'cube', last_spec_cubemap, spec_cubemap)
    process(args, None)
    
    generated_mipmaps.append(spec_cubemap)
    last_spec_cubemap = spec_cubemap

# 4. prefilter the environment
prefiltered_mipmaps = []
prefilter_input = "/data/out/spec/specular_cubemap_%d.tiff"
prefilter_output = "/data/out/spec/prefilter_specular"
args = env_tool_args + ('envPrefilter', '-s', '512', '-n', '4096', '-r', '1', prefilter_input, prefilter_output)
process(args, f"prefiltered cubemap from {prefilter_input} to {prefilter_output}")

for m in generated_mipmaps:
    m = m.replace('specular_cubemap_', 'prefilter_specular_')
    m = m.replace('tiff', 'tif')
    prefiltered_mipmaps.append(m)

# 5. generate the irradiance map
irr_cubemap = "data/out/irr_cubemap.tiff"
args = env_tool_args + ('envIrradiance', '-n', '256', hres_cubemap, irr_cubemap)
process(args, f"{irr_cubemap} from {hres_cubemap}")

# 6. unpack the cubemap faces
def unpack_cubemap(input_file, out_dir, output_name, mipmaps):
    print(f"Unpacking {input_file} faces...")
    CUBE_FACES = "right left top bottom front back".split()

    if mipmaps:
        mipmaps_re = re.compile("^.+?(\d+)\.tiff?")
        match = next(mipmaps_re.finditer(str(input_file)))
        mipmap_level = "_" + match.group(1)
    else:
        mipmap_level = ""

    face_names = []

    for i, face in enumerate(CUBE_FACES):
        out = f"data/out/{out_dir}/{output_name}_{face}{mipmap_level}.png"
        args = env_tool_args + ('oiiotool', '--subimage', str(i), input_file, '-o', out)
        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        process.communicate()

        face_names.append(out)

    return face_names

specular_faces = []
for m in prefiltered_mipmaps:
    faces = unpack_cubemap(m, "spec/faces", "specular", mipmaps=True)
    specular_faces.extend(faces)

irr_faces = []
irr_faces = unpack_cubemap(irr_cubemap, "irr_faces", "irr_cubemap", mipmaps=False)

# 7. give ownership of the generated files. TODO: check how this works out on Windows
if platform.system() != "Windows":
    print(f"\nGiving ownership...\n")
    faces = specular_faces + irr_faces + generated_mipmaps + prefiltered_mipmaps + [hres_cubemap, irr_cubemap, original_panorama]
    args = env_tool_args + ('chown', str(getuid()), *faces)
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    process.communicate()

#
# Note: Compressing to ktx and repacking to cubemap are done by "compress_image.py" and "ktxmerge.py" respectively
#
