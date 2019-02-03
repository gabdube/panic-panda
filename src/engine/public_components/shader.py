import json
from pathlib import Path
from ..base_types import name_generator, UniformsMaps, Id, AnimationChannelSupport, ShaderScope


SHADER_ASSET_PATH = Path("./assets/shaders/")
shader_name = name_generator("Shader")


class Shader(object):

    def __init__(self, vert, frag, mapping, **kwargs):
        self._id = Id()
        self.name = kwargs.get('name', next(shader_name))
        self.vert = vert
        self.frag = frag
        self.mapping = mapping
        
        # Attributes names listed in here will be ignored by the data shader
        self.disabled_attributes = set()

        # Animation support by the shader
        self.has_timer = False
        self.channels = AnimationChannelSupport(0)
        self._parse_animation_support(mapping)

        # Uniform collection for the shader. Can be preinitialized with user data before loading the shader in a scene
        # Afterwards, the object will contain device data. Uniform are prepared in `DataScene._setup_uniforms` 
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

    def toggle_attribute(self, name, value):
        attr = self.disabled_attributes
        if not value and name in attr:
            attr.remove(name)
        else:
            attr.add(name)

    def set_constant(self, name, value):
        constants = self.mapping["constants"]
        constant = next((c for c in constants if c["name"] == name), None)
        if constant is None:
            raise ValueError(f"No shader constant named \"{name}\" in shader")

        constant["default_value"] = value

    def _parse_animation_support(self, mapping):

        # Validate the sets
        animation_sets = [s for s in mapping['sets'] if s['scope'] == ShaderScope.ENGINE_TIMER]
        sets_count = len(animation_sets)
        if sets_count > 1:
            raise ValueError(f"Only one set must have the \"engine animation\" scope, found {sets_count}.")
        elif sets_count == 0:
            return

        # Validate the uniforms
        set_id = animation_sets[0]['id']
        animation_uniforms = [u for u in mapping['uniforms'] if u['set'] == set_id]
        uniforms_count = len(animation_uniforms)
        if uniforms_count > 2:
            raise ValueError(f"A maximum of 2 binding can be allocated for the animations uniforms, found {uniforms_count}")
        elif uniforms_count == 0:
            return

        # Check the uniform names
        uniform_names = [u['name'] for u in animation_uniforms]
        for name in ('timer', 'channels'):
            if name in uniform_names:
                uniform_names.remove(name)

        if len(uniform_names) != 0:
            print(f"Warning! Some uniform binding for the animations are not recognized ({uniform_names}). Make sure they are named 'timer' and 'channels'")

        # Parse the uniform bindings
        self._parse_animation_timer(animation_uniforms)
        if self.has_timer:
            self._parse_animation_channels(animation_uniforms)

    def _parse_animation_timer(self, uniforms):
        timer_uniform = next((u for u in uniforms if u['name'] == 'timer'), None)
        if timer_uniform is None:
            return

        self.has_timer = True

    def _parse_animation_channels(self, uniforms):
        channel_uniform = next((u for u in uniforms if u['name'] == 'channels'), None)
        if channel_uniform is None:
            return
