import json
from pathlib import Path
from ..base_types import name_generator, UniformsMaps, Id


SHADER_ASSET_PATH = Path("./assets/shaders/")
compute_name = name_generator("Compute")

class Compute(object):

    def __init__(self, src, mapping, **kwargs):
        self._id = Id()
        self.name = kwargs.get('name', next(compute_name))
        self.src = src
        self.mapping = mapping
        self.uniforms = UniformsMaps()
        self.queue = kwargs.get('queue')

    @classmethod
    def from_file(cls, src, mapping, **kwargs):
        shader = super().__new__(cls)
        src_spv = mapping_json = None

        with open(SHADER_ASSET_PATH / src, 'rb') as f:
            src_spv = f.read()

        with open(SHADER_ASSET_PATH / mapping, 'r') as f:
            mapping_json = json.load(f)

        shader.__init__(src_spv, mapping_json, **kwargs)

        return shader

    def set_constant(self, name, value):
        constants = self.mapping["constants"]
        constant = next((c for c in constants if c["name"] == name), None)
        if constant is None:
            raise ValueError(f"No shader constant named \"{name}\" in shader")

        constant["default_value"] = value
