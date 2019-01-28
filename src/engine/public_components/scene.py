from . import Shader, Mesh, GameObject, Image, Sampler, Compute, Animation
from ..base_types import Id


class Scene(object):

    def __init__(self):
        self._id = Id()
        self.shaders = ComponentArray(Shader)
        self.computes = ComponentArray(Compute)
        self.meshes = ComponentArray(Mesh)
        self.objects = ComponentArray(GameObject)
        self.samplers = ComponentArray(Sampler)
        self.images = ComponentArray(Image)
        self.animations = ComponentArray(Animation)
        self.update_obj_set = set()
        self.update_shader_set = set()

        empty = lambda: None
        empty_w_events = lambda x, y: None
        self.on_initialized = empty
        self.on_window_resized = empty_w_events
        self.on_mouse_move = empty_w_events
        self.on_mouse_click = empty_w_events
        self.on_key_pressed = empty_w_events
        self.on_mouse_scroll = empty_w_events

    @classmethod
    def empty(cls):
        scene = super().__new__(cls)
        scene.__init__()
        return scene

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id.value = value

    @property
    def loaded(self):
        return self._id.value is not None

    def update_objects(self, *objects):
        self.update_obj_set.update(set(obj for obj in objects if isinstance(obj, GameObject)))

    def update_shaders(self, *shaders):
        self.update_shader_set.update(set(shader for shader in shaders if isinstance(shader, (Shader, Compute))))


class ComponentArray(list):

    def __init__(self, component_type):
        self.component_type = component_type

    def append(self, i):
        if not isinstance(i, self.component_type):
            raise TypeError(f"Item type must be {self.component_type.__qualname__}, got {type(i)}")

        i.id = len(self)
        super().append(i)

    def extend(self, *items):
        offset = 0
        for i in items:
            if not isinstance(i, self.component_type):
                raise TypeError(f"Item type must be {self.component_type.__qualname__}, got {type(i)}")
            i.id = len(self) + offset
            offset += 1

        super().extend(items)

    def __repr__(self):
        return f"{self.component_type.__qualname__}({super().__repr__()})"

