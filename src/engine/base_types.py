from collections import namedtuple

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
        

class UniformsMaps(object):

    # Used to filter out non data fields when initializing uniforms in `DataScene._setup_uniforms`
    _NON_UNIFORM_NAMES = ('as_dict', 'bound', 'merge', 'uniform_names', 'updated_member_names')

    def __init__(self):
        self.updated_member_names = set()
        self.uniform_names = []
        self.bound = False

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
            for name, ctype in uni._fields_:
                value = getattr(uni, name)
                if hasattr(value, '_length_'):
                    fields[name] = value[::]
                else:
                    fields[name] = value
        
        return d

    def __getattribute__(self, name):
        sup = super()
        names = sup.__getattribute__("uniform_names")
        
        if name in names:
            sup.__getattribute__("updated_member_names").add(name)

        return sup.__getattribute__(name)
