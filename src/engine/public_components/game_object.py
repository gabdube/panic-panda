from ..base_types import name_generator, UniformsMaps, Id

obj_name = name_generator("Object")


class GameObject(object):

    def __init__(self, **kwargs):
        self._id = Id()
        self.name = kwargs.get('name', next(obj_name))
        self.shader = None
        self.mesh = None
        self.uniforms = UniformsMaps()
        self.hidden = kwargs.get('hidden', False)

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id.value = value

    @classmethod
    def from_components(cls, shader, mesh, **kwargs):
        obj = super().__new__(cls, **kwargs)
        obj.__init__(**kwargs)
        obj.shader = shader
        obj.mesh = mesh
        return obj
