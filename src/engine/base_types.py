from collections import namedtuple
from enum import IntFlag, Enum


Queue = namedtuple("Queue", ("handle", "family"))
ImageAndView = namedtuple("ImageAndView", ("image", "view"))

def name_generator(base):
    i = 0
    while True:
        i += 1
        yield f"{base}_{i}"


class Id(object):

    __slots__ = ('value',)

    def __init__(self):
        self.value = None

    def __index__(self):
        return self.value
    
    def __int__(self):
        return self.value

    def __repr__(self):
        return f"ID({self.value})"
        

class UniformsMaps(object):

    # Used to filter out non data fields when initializing uniforms in `DataScene._setup_uniforms`
    _NON_UNIFORM_NAMES = ('as_dict', 'bound', 'merge', 'uniform_names', 'updated_member_names')

    def __init__(self):
        sup = super()
        sup.__setattr__('updated_member_names', set())
        sup.__setattr__('uniform_names', [])
        sup.__setattr__('bound', False)

    def merge(self, **values):
        if self.bound:
            raise NotImplementedError()
        else:
            for name, value in values.items():
                setattr(self, name, value)

    def as_dict(self):
        d = {}
        for n in self.uniform_names:
            uni = super().__getattribute__(n)
            d[n] = fields = {}

            if hasattr(uni, '_fields_'):
                for name, ctype in uni._fields_:
                    value = getattr(uni, name)
                    if hasattr(value, '_length_'):
                        fields[name] = value[::]
                    else:
                        fields[name] = value
            else:
                d[n] = uni
        
        return d

    def __getattribute__(self, name):
        sup = super()
        names = sup.__getattribute__("uniform_names")

        if name in names:
            sup.__getattribute__("updated_member_names").add(name)

        return sup.__getattribute__(name)

    def __setattr__(self, name, value):
        sup = super()
        names = sup.__getattribute__("uniform_names")

        if name in names:
            sup.__getattribute__("updated_member_names").add(name)
        
        sup.__setattr__(name, value)


class AnimationChannelSupport(IntFlag):
    Translation = 2
    Rotation = 3
    Scale = 4
    Weigth = 5


class UniformMemberType(Enum):
    FLOAT_MAT2 = 0
    FLOAT_MAT3 = 1
    FLOAT_MAT4 = 2

    FLOAT_VEC2 = 3
    FLOAT_VEC3 = 4
    FLOAT_VEC4 = 5

    INT_MAT2 = 6
    INT_MAT3 = 7
    INT_MAT4 = 8

    INT_VEC2 = 9
    INT_VEC3 = 10
    INT_VEC4 = 11

    FLOAT = 12
    INT = 13
    BOOL = 14


class ShaderScope(Enum):
    # Allocate a descriptor set per shader
    GLOBAL = 0

    # Allocate a descriptor set per object linked to a shader
    LOCAL = 1

    # Allocate a descriptor set per object linked to the shader
    # Data is managed by the engine
    ENGINE_TIMER = 2

    # Allocate a descriptor set per object.
    # Data is managed b the engine
    ENGINE_ANIMATIONS = 3


class AnimationNames(object):
    TIMER_NAME = "timer"

    CHANNELS_NAME = "channels"
    TRANSLATION_NAME = "translation"
    ROTATION_NAME = "rotation"
    SCALE_NAME = "scale"

    INTERPOLATION_SUFFIX = "_interpolation"


class AnimationInterpolation(Enum):
    Linear = 1
    Step = 2
    CubicSpline = 3
