"""
This script process .hdr/.exr/.tif environment map files into a specular cubemap and a irradiance cubemap.
The images are then processed by the "compress_images" script and then (FINALLY), the generated .ktx files
are processed by "ktxmerge.py" to create two ktx cubemap.

TODO: just send one list of commands to docker instead of calling it a bajillion times

Dependencies:

* envtool [ https://github.com/cedricpinson/envtools ] it is assumed that the tool was installed with docker
* pillow (PIL fork) [ https://pillow.readthedocs.io/en/5.3.x/ ]

Usage:

`python compile_environment.py --path PATH --input INPUT`
"""

from pathlib import Path
from PIL import Image
from os import getuid
import sys, subprocess, platform

argv = sys.argv

path_index = argv.index("--path")
path = Path(argv[path_index+1]).resolve()

input_index = argv.index("--input")
input_env = argv[input_index+1]
input_env_docker = "data/"+input_env

def process(args, text):
    global output 

    print(f"\nGenerating {text}")
    print(" ".join(args))
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    process.communicate()
    print(f"Generated {text}\n")


# Prepare the shared space between docker and the host
out_path = path/"out"
out_path.mkdir(exist_ok=True)
env_tool_args = ("docker", "run",  "-v", f"{path}:/data", "-t", "trigrou/envtools")


# 1. generate a .tif panorama from the input file
original_panorama = "data/out/original_panorama.tiff"
args = env_tool_args + ('oiiotool', '-v', input_env_docker, '--clamp:max=1040.0', '--clamp:min=0', '-o', original_panorama)
process(args, f"{original_panorama} from {input_env}")

# 2. generate a high quality cubemap
hres_cubemap = "data/out/highres_cubemap.tiff"
args = env_tool_args + ('envremap', '-p', 'rgss', '-o', 'cube', original_panorama, hres_cubemap)
process(args, f"{hres_cubemap} from {original_panorama}")

# 3. generate the irradiance map
irr_cubemap = "data/out/irr_cubemap.tiff"
args = env_tool_args + ('envIrradiance', '-n', '256', hres_cubemap, irr_cubemap)
process(args, f"{irr_cubemap} from {hres_cubemap}")

# 4. unpack the cubemap faces
def unpack_cubemap(input_file, output_name):
    print(f"Unpacking {input_file} faces...")
    CUBE_FACES = "right left top bottom front back".split()
    face_names = []

    for i, face in enumerate(CUBE_FACES):
        out = f"data/out/{output_name}_{face}.png"
        args = env_tool_args + ('oiiotool', '--subimage', str(i), input_file, '-o', out)
        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        process.communicate()

        face_names.append(out)

    return face_names

hires_faces = unpack_cubemap(hres_cubemap, "highres_cubemap")
irr_faces = unpack_cubemap(irr_cubemap, "irr_cubemap")

# 5. give ownership of the generated files. TODO: check how this works out on Windows
if platform.system() != "Windows":
    print(f"\nGiving ownership...\n")
    faces = hires_faces+irr_faces
    args = env_tool_args + ('chown', str(getuid()), *faces)
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    process.communicate()

# 6. Compress the images


#env_files = unpack_cubemap(path / "out" / "highres_cubemap.tiff")
#irr_files = unpack_cubemap(path / "out" / "irr_cubemap.tiff")
