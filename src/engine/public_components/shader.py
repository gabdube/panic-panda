import json
from pathlib import Path


SHADER_ASSET_PATH = Path("./assets/shaders/")

class Shader(object):

    def __init__(self, vert, frag, mapping):
        self.id = None
        self.vert = vert
        self.frag = frag
        self.mapping = mapping

    @classmethod
    def from_files(cls, vert, frag, mapping):
        shader = super().__new__(cls)
        shader.id = None

        vert_spv = frag_spv = mapping_json = None

        with open(SHADER_ASSET_PATH / vert, 'rb') as f:
            vert_spv = f.read()

        with open(SHADER_ASSET_PATH / frag, 'rb') as f:
            frag_spv = f.read()

        with open(SHADER_ASSET_PATH / mapping, 'r') as f:
            mapping_json = json.load(f)

        shader.__init__(vert_spv, frag_spv, mapping_json)

        return shader
