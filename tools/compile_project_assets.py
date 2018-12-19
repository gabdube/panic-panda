"""
A script that compile the resources used in the project.
Must be called from the root project folder and python must be in your path.

if "--commands" is passed to the script, the script will output the commands used WITHOUT executing them.
This is usefull if you only want to compile a certain asset

"""

from pathlib import Path
import subprocess, shutil, sys

# Testing if we are in the project root
if not Path('./assets/').is_dir():
    raise ValueError("This script must be started from the project root dir")

COMPILE_SHADER_PATH = "./tools/compile_shaders.py"
COMPRESS_IMAGES_PATH = "./tools/compress_images.py"
KTX_MERGE_PATH = "./tools/ktxmerge.py"

SHADERS_PATH = Path("./assets/shaders")
IMAGES_PATH = Path("./assets/images")

ONLY_COMMANDS = "--commands" in sys.argv

MAX_SUBPROCESSES = 5
OUTPUT = ""

def wait_subprocesses(outputs):
    global OUTPUT

    if ONLY_COMMANDS:
        return

    print(f"WAITING FOR {tuple(outputs.keys())}")

    for name, process in outputs.items():
        OUTPUT += f"\n{name}\n" + (process.communicate()[0]).decode("utf8")

    outputs.clear()

def process(*inputs):
    global OUTPUT

    if ONLY_COMMANDS:
        OUTPUT += " ".join(inputs) + "\n"
    else:
        return subprocess.Popen(inputs, stdout=subprocess.PIPE)


shaders = (
    (SHADERS_PATH/"debug_texture", "debug_texture"),
    (SHADERS_PATH/"debug_texture_array", "debug_texture_array"),
    (SHADERS_PATH/"debug_texture_cube", "debug_texture_cube"),
    (SHADERS_PATH/"main", "main"),
)


images = (
    (IMAGES_PATH/"dev", "brdfLUT.png"),
    (IMAGES_PATH/"dev/array_test", "*.png"),
    (IMAGES_PATH/"dev/papermill/diffuse", "*.png"),
    (IMAGES_PATH/"dev/papermill/specular", "*.png")
)


images_merge_copy = (
    ("MOVE", IMAGES_PATH/"dev/brdfLUT.ktx", IMAGES_PATH/"brdfLUT.ktx"),
    ("MERGE_ARRAY", IMAGES_PATH/"dev/array_test/*", IMAGES_PATH/"array_test.ktx"),
    ("MERGE_CUBE", IMAGES_PATH/"dev/papermill/diffuse/*", IMAGES_PATH/"papermill_diffuse.ktx"),
    ("MERGE_CUBE_MIPS", IMAGES_PATH/"dev/papermill/specular/*", IMAGES_PATH/"papermill_specular.ktx"),
)


#
# SHADERS!
#
shaders_outputs = {}
for shader_path, shader_name in shaders:
    p = process("python", COMPILE_SHADER_PATH, "--path", str(shader_path), "--input", shader_name)
    if p is not None:
        shaders_outputs[f"[SHADER {shader_name}]"] = p 

    if len(shaders_outputs) > MAX_SUBPROCESSES:
        wait_subprocesses(shaders_outputs)

wait_subprocesses(shaders_outputs)

#
# IMAGES!
#
images_outputs = {}
for image_path, image_name in images:
    p = process("python", COMPRESS_IMAGES_PATH, "--path", str(image_path), "--input", image_name)
    if p is not None:
        images_outputs[f"[IMAGE {image_path}/{image_name}]"] = p 

    if len(images_outputs) > MAX_SUBPROCESSES:
        wait_subprocesses(images_outputs)

wait_subprocesses(images_outputs)

#
# IMAGES MERGING & MOVING!
#
merge_outputs = {}
for action, target, output in images_merge_copy:
    p = None

    if action == "MOVE" and not ONLY_COMMANDS:
        shutil.move(target, output)
    elif action == "MERGE_ARRAY":
        p = process("python", KTX_MERGE_PATH,  "--array", "--auto", "--output", str(output), "--input", str(target))
    elif action == "MERGE_CUBE":
        p = process("python", KTX_MERGE_PATH,  "--cube", "--auto", "--output", str(output), "--input", str(target))
    elif action == "MERGE_CUBE_MIPS":
        p = process("python", KTX_MERGE_PATH,  "--cube", "--auto", "--mipmaps", "--output", str(output), "--input", str(target))

    if p is not None:
        merge_outputs[f"[{action} {target}]"] = p 

    if len(merge_outputs) > MAX_SUBPROCESSES:
        wait_subprocesses(merge_outputs)

wait_subprocesses(merge_outputs)

#
# IMAGE CLEANING!
#
clean = (
    (IMAGES_PATH/"dev/array_test/", "*.ktx"),
    (IMAGES_PATH/"dev/papermill/diffuse", "*.ktx"),
    (IMAGES_PATH/"dev/papermill/specular", "*.ktx"),
)

if not ONLY_COMMANDS:
    for path, pattern in clean:
        for path in path.glob(pattern):
            path.unlink()

#
# Printing outputs
#

print()
print(OUTPUT)
