from . import Shader, Mesh, GameObject, Image, Sampler


class Scene(object):

    def __init__(self):
        self.id = None
        self.shaders = ComponentArray(Shader)
        self.meshes = ComponentArray(Mesh)
        self.objects = ComponentArray(GameObject)
        self.samplers = ComponentArray(Sampler)
        self.images = ComponentArray(Image)
        self.update_obj_set = set()
        self.update_shader_set = set()

        empty = lambda: None
        empty_w_events = lambda x, y: None
        self.on_initialized = empty
        self.on_window_resized = empty_w_events
        self.on_mouse_move = empty_w_events
        self.on_mouse_click = empty_w_events

    @classmethod
    def empty(cls):
        scene = super().__new__(cls)
        scene.__init__()
        return scene

    def update_objects(self, *objects):
        self.update_obj_set.update(set(obj for obj in objects if isinstance(obj, GameObject)))

    def update_shaders(self, *shaders):
        self.update_shader_set.update(set(shader for shader in shaders if isinstance(shader, Shader)))


class ComponentArray(list):

    def __init__(self, component_type):
        self.component_type = component_type

    def append(self, i):
        if not isinstance(i, self.component_type):
            raise TypeError(f"Item type must be {self.component_type.__qualname__}, got {type(i)}")

        i.id = len(self)
        super().append(i)

    def __repr__(self):
        return f"{self.component_type.__qualname__}({super().__repr__()})"

