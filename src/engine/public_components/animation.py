from engine.assets import GLBFile, GLTFFile
from ..base_types import name_generator, Id
from enum import Enum

anim_name = name_generator("Animation")


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
        self.name = kwargs.get('name', next(anim_name))

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

        print("\n\n")

        animation_data_accessors = {}
        for cs in channel_samplers:
            input_data = gltf_file.accessor_data(cs["input"])
            output_data = gltf_file.accessor_data(cs["output"])

            print(input_data)
            print(output_data)
            
        print(channel_samplers)
        print()

        anim = super().__new__(cls)
        anim.__init__(**kwargs)
        return anim
