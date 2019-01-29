from engine.assets import GLBFile, GLTFFile
from ..base_types import name_generator, Id
from enum import Enum

anim_name = name_generator("Animation")


class AnimationPlayback(Enum):
    Once = 0
    Loop = 1


class Interpolation(Enum):
    Linear = 0
    Step = 1
    CubicSpline = 2

    @staticmethod
    def from_string(v):
        v = v.lower().capitalize()
        return getattr(Interpolation, v)


class Path(Enum):
    Translation = 0
    Rotation = 1
    Scale = 2
    Weights = 3

    @staticmethod
    def from_string(v):
        v = v.lower().capitalize()
        return getattr(Path, v)


class Animation(object):

    def __init__(self, **kwargs):
        self._id = Id()
        self.bound = False
        self.name = kwargs.get('name', next(anim_name))
        self.channel_samplers = []
        self.animation_inputs = {}
        self.animations_outputs = {}

    @classmethod
    def from_gltf(cls, gltf_file, index, **kwargs):
        
        if not (isinstance(gltf_file, GLBFile) or isinstance(gltf_file, GLTFFile)):
            raise TypeError(f"Unknown/Unsupported type: {type(gltf_file).__qualname__}") 

        animation = gltf_file.layout['animations'][index]
        channels = animation['channels']
        samplers = animation['samplers']

        channel_samplers = []
        for channel in channels:
            sampler = samplers[channel['sampler']]

            channel_sampler = channel.copy()
            channel_sampler.update(sampler)
            channel_sampler.update(channel['target'])

            # Parse enum values
            channel_sampler['interpolation'] = Interpolation.from_string(channel_sampler['interpolation'])
            channel_sampler['path'] = Path.from_string(channel_sampler['path'])

            # Delete superfluous information
            del channel_sampler['target']
            del channel_sampler['node']
            del channel_sampler['sampler']

            channel_samplers.append(channel_sampler)

        animations_inputs = {}
        animations_outputs = {}
        for cs in channel_samplers:
            _input, _output = cs["input"], cs["output"]
            input_data = gltf_file.accessor_data(_input)
            output_data = gltf_file.accessor_data(_output)

            animations_inputs[_input] = input_data
            animations_outputs[_output] = output_data

        anim = super().__new__(cls)
        anim.__init__(**kwargs)
        anim.channel_samplers = channel_samplers
        anim.animations_inputs = animations_outputs
        anim.animations_outputs = animations_outputs
        return anim

    def play(self, target, playback = AnimationPlayback.Once):
        if not self.bound:
            raise ValueError("Impossible to play an animation that is not yet fully loaded in the engine")
