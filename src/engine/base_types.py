from collections import namedtuple

Queue = namedtuple("Queue", ("handle", "family"))
ImageAndView = namedtuple("ImageAndView", ("image", "view"))

def name_generator(base):
    i = 0
    while True:
        i += 1
        yield f"{base}_{i}"

class UniformsMaps(object):

    def __init__(self):
        self.updated_member_names = set()
        self.uniform_names = []

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
