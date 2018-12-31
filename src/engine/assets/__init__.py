from pathlib import Path

MODEL_PATH = Path("./assets/models/")
IMAGE_PATH = Path("./assets/images/")

from .shared import *
from .glb_file import GLBFile
from .gltf_file import GLTFFile
from .ktx_file import KTXFile
from .env_cubemap_file import EnvCubemapFile
