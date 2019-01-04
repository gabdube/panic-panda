"""
Utility to quickly compress image in this project.
Uses "Compressonator" (the CLI tool, not the GUI) from https://github.com/GPUOpen-Tools/Compressonator

Note that compressonator don't like when you try to compress 200 images simultaneously, hence the subprocess limit.

Usage:

-- Simple compression
1 - Make sure `CLI_PATH` points to the right binary
2 - `python ./tools/compress_images.py --path PATH --input *.png`

"""

from pathlib import Path
import sys, subprocess

argv = sys.argv

CLI_PATH = "CompressonatorCLI-bin"
MAX_SUBPROCESS = 3
OUTPUT = ""

help = "--help" in argv or "-h" in argv

if not help:
    path_index = argv.index("--path")
    path = Path(argv[path_index+1])

    input_index = argv.index("--input")
    pattern = argv[input_index+1]

arguments = ["-log", "-fd", "BC7"]

mipsize = "--miplevels" in argv
if mipsize:
    mipsize = argv[argv.index("--miplevels")+1]
    arguments.extend(('-miplevels', mipsize))

outputs = {}

def wait_subprocesses():
    global OUTPUT, outputs

    print(f"WAITING FOR {tuple(outputs.keys())}")

    for name, process in outputs.items():
        OUTPUT += f"\n{name}\n" + (process.communicate()[0]).decode("utf8")

    outputs.clear()

def process_simple():

    for file in path.glob(pattern):
        suffix = file.suffix
        file_in = str(file)
        file_out = file_in[:-len(suffix)] + ".ktx"

        p = subprocess.Popen([CLI_PATH, *arguments, file_in, file_out], stdout=subprocess.PIPE)
        outputs[file.name] = p

        if len(outputs) > MAX_SUBPROCESS:
            wait_subprocesses()

def process_help():
    p = subprocess.Popen([CLI_PATH], stdout=subprocess.PIPE)
    outputs["HELP"] = p

if not help:
    process_simple()
else:
    process_help()

wait_subprocesses()

print(OUTPUT)
