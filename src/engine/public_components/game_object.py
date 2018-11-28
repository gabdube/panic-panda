from ..base_types import name_generator, UniformsMaps

obj_name = name_generator("Object")


class GameObject(object):

    def __init__(self, **kwargs):
        self.id = None
        self.name = kwargs.get('name', next(obj_name))
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
