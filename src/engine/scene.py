from . import Shader, Mesh, GameObject


class Scene(object):

    def __init__(self):
        self.__shaders = ComponentArray(Shader)
        self.__meshes = ComponentArray(Mesh)
        self.__objects = ComponentArray(GameObject)

    @classmethod
    def empty(cls):
        scene = super().__new__(cls)
        scene.__init__()
        return scene

    @property
    def shaders(self):
        return self.__shaders

    @property
    def meshes(self):
        return self.__meshes

    @property
    def objects(self):
        return self.__objects


class ComponentArray(list):

    def __init__(self, component_type):
        self.component_type = component_type

    def append(self, i):
        if not isinstance(i, self.component_type):
            raise TypeError(f"Item type must be {self.component_type.__qualname__}, got {type(i)}")

        super().append(i)

    def __repr__(self):
        return f"{self.component_type.__qualname__}({super().__repr__()})"

