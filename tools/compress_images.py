"""
Utility to quickly compress image in this project.
Uses "Compressonator" (the CLI tool, not the GUI) from https://github.com/GPUOpen-Tools/Compressonator

Usage:
1 - Make sure `CLI_PATH` points to the right binary
2 - `python .\compress_images.py *.png`
"""

from pathlib import Path
import sys, subprocess

CLI_PATH = "C:/Program Files/Compressonator 3.1.4064/bin/CLI/CompressonatorCLI.exe"
BASE_PATH = Path("../assets/images/")

pattern = sys.argv[1]
arguments = ["-fd", "BC7"]

outputs = {}

for file in BASE_PATH.glob(pattern):
    suffix = file.suffix
    file_in = str(file)
    file_out = file_in[:-len(suffix)] + ".ktx"

    subprocess.check_output([CLI_PATH, *arguments, file_in, file_out])
