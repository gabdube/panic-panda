import json
from pathlib import Path
from ..base_types import name_generator, UniformsMaps, Id, AnimationChannelSupport, ShaderScope, AnimationNames


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
        names = AnimationNames
        scope = ShaderScope

        # Validate the timer set
        timer_sets = [s for s in mapping['sets'] if s['scope'] == scope.ENGINE_TIMER.value]
        timer_sets_count = len(timer_sets)
       
        # Validate the channels set
        channel_sets = [s for s in mapping['sets'] if s['scope'] == scope.ENGINE_ANIMATIONS.value]
        channel_sets_count = len(channel_sets)

        if timer_sets_count > 1:
            raise ValueError(f"Only one set must have the \"ENGINE_TIMER\" scope, found {timer_sets_count}.")
        elif timer_sets_count == 0:
            return
        elif channel_sets_count > 1:
            raise ValueError(f"Only one set must have the \"ENGINE_ANIMATIONS\" scope, found {channel_sets_count}.")


        # Validate the uniforms
        timer_set_id = timer_sets[0]['id']
        timer_uniforms = [u for u in mapping['uniforms'] if u['set'] == timer_set_id]

        channel_set_id = None if channel_sets_count == 0 else channel_sets[0]['id']
        channel_uniforms = [u for u in mapping['uniforms'] if u['set'] == channel_set_id]
        
        if len(timer_uniforms) != 1:
            raise ValueError(f"The timer descriptor set must only have one binding named `{names.TIMER_NAME}`")
        elif len(channel_uniforms) > 1:
            raise ValueError(f"The channels descriptor set must only have one binding named `{names.CHANNELS_NAME}`")

        # Check the names
        timer_uniform_name = timer_uniforms[0]['name']
        if timer_uniform_name != names.TIMER_NAME:
            raise ValueError(f"The timer uniform name must be \"{names.TIMER_NAME}\", got \"{timer_uniform_name}\" ")

        if channel_set_id is not None:
            channel_uniform = channel_uniforms[0]
            if channel_uniform['name'] != names.TIMER_NAME:
                raise ValueError(f"The channel uniform name must be \"{names.CHANNELS_NAME}\", got \"{channel_uniform['name']}\" ")

            valid_member_names = names.CHANNEL_MEMBERS
            bad_member_names = [f["name"] for f in channel_uniform['fields'] if f not in valid_member_names] 
            if len(bad_member_names) > 0:
                msg = f"Some member names of the animation channel uniform are not valid: {bad_member_names}. Valid values: {valid_member_names}"
                raise ValueError(msg)
        else:
            channel_uniform = None

        self._parse_animation_timer(timer_uniforms)
        if self.has_timer and channel_uniform is not None:
            self._parse_animation_channels(channel_uniform)

    def _parse_animation_timer(self, uniforms):
        timer_uniform = next((u for u in uniforms if u['name'] == 'timer'), None)
        if timer_uniform is None:
            return

        self.has_timer = True

    def _parse_animation_channels(self, channel_uniform):
        fields_name = [f["name"] for f in channel_uniform['fields']]
        print(fields_name)
        raise NotImplementedError()
        

