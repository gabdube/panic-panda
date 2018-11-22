class GameObject(object):

    def __init__(self):
        self.id = None
        self.shader = None
        self.mesh = None
        self.uniforms = UniformsMaps()

    @classmethod
    def from_components(cls, shader, mesh):
        obj = super().__new__(cls)
        obj.__init__()
        obj.shader = shader
        obj.mesh = mesh
        return obj


class UniformsMaps(object):

    def __init__(self):
        self.updated_member_names = set()
        self.uniform_names = []

    def __getattribute__(self, name):
        sup = super()
        names = sup.__getattribute__("uniform_names")
        
        if name in names:
            sup.__getattribute__("updated_member_names").add(name)

        return sup.__getattribute__(name)
