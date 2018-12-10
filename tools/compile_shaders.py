"""
Compile the shaders found in the asset shaders directory using glslangValidator. 
glslangValidator must be in your PATH.

Usage:
1 - Make sure that `glslangValidator` is in your path
2 - `python .\compile_shaders.py main`
"""

from pathlib import Path
from io import StringIO
import sys, subprocess

BASE_PATH = Path("../assets/shaders/")

pattern = "**/*"
if len(sys.argv) > 1:
    pattern = f"**/{sys.argv[1]}.*"


outputs = {}

for file in BASE_PATH.glob(pattern):
    if file.suffix not in ('.frag', '.vert'):
        continue

    file_in = str(file)
    file_out = str(file_in) + '.spv'

    p = subprocess.Popen(["glslangValidator", "-V", file_in, "-o", file_out], stdout=subprocess.PIPE)
    outputs[file.name] = p.communicate()[0]

print()
for name, output in outputs.items():
    print(name)
    print(output.decode('utf8'))
