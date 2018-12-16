"""
Utility to quickly compress image in this project.
Uses "Compressonator" (the CLI tool, not the GUI) from https://github.com/GPUOpen-Tools/Compressonator

Usage:

-- Simple compression
1 - Make sure `CLI_PATH` points to the right binary
2 - `python ./tools/compress_images.py --path PATH --input *.png`

"""

from pathlib import Path
import sys, subprocess

argv = sys.argv

CLI_PATH = "C:/Program Files/Compressonator 3.1.4064/bin/CLI/CompressonatorCLI.exe"

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

print(arguments)
outputs = {}

def process_simple():

    for file in path.glob(pattern):
        suffix = file.suffix
        file_in = str(file)
        file_out = file_in[:-len(suffix)] + ".ktx"

        p = subprocess.Popen([CLI_PATH, *arguments, file_in, file_out], stdout=subprocess.PIPE)
        outputs[file.name] = p.communicate()[0]

def process_cube():
    pass

def process_help():
    p = subprocess.Popen([CLI_PATH], stdout=subprocess.PIPE)
    outputs["HELP"] = p.communicate()[0]

if not help:
    process_simple()
else:
    process_help()

print()
for name, output in outputs.items():
    print(name)
    print(output.decode('utf8'))
