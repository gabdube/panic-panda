import json
from pathlib import Path
from ..base_types import name_generator, UniformsMaps, Id


SHADER_ASSET_PATH = Path("./assets/shaders/")
shader_name = name_generator("Shader")


class Shader(object):

    def __init__(self, vert, frag, mapping, **kwargs):
        self._id = Id()
        self.name = kwargs.get('name', next(shader_name))
        self.vert = vert
        self.frag = frag
        self.mapping = mapping

        self.uniforms = UniformsMaps()

    @classmethod
    def from_files(cls, vert, frag, mapping, **kwargs):
        shader = super().__new__(cls)

        vert_spv = frag_spv = mapping_json = None

        with open(SHADER_ASSET_PATH / vert, 'rb') as f:
            vert_spv = f.read()

        with open(SHADER_ASSET_PATH / frag, 'rb') as f:
            frag_spv = f.read()

        with open(SHADER_ASSET_PATH / mapping, 'r') as f:
            mapping_json = json.load(f)

        shader.__init__(vert_spv, frag_spv, mapping_json, **kwargs)

        return shader

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id.value = value
