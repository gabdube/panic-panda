from engine import Scene, Shader, Mesh, Image, Sampler, GameObject, CombinedImageSampler
from engine.assets import KTXFile, GLTFFile, IMAGE_PATH
from system import events as evt
from utils import Mat4
from vulkan import vk
from .components import Camera, LookAtView
from math import radians, sin, cos


class DebugComputeScene(object):

    def __init__(self, app, engine):
        self.app = app
        self.engine = engine
        self.scene = s = Scene.empty()

        # Global state stuff
        self.shaders = ()
        self.objects = ()
        self.debug = 0

        # Camera
        width, height = engine.window.dimensions()
        self.camera = cam = Camera(45, width, height)
        self.camera_view = LookAtView(cam, position = [0,0,-3.5], bounds_zoom=(-7.0, -0.2))

        # Assets
        self._setup_assets()

        # Callbacks
        s.on_initialized = self.init_scene
        s.on_window_resized = self.update_perspective
        s.on_key_pressed = self.handle_keypress
        s.on_mouse_move = s.on_mouse_click = s.on_mouse_scroll = self.handle_mouse

    def init_scene(self):
        self.update_objects()
        self.update_view()
        
    def update_perspective(self, event, data):
        width, height = data
        self.camera.update_perspective(60, width, height)
        self.update_objects()

    def update_view(self):
        return

    def update_objects(self):
        objects = self.objects
        view = self.camera.view
        projection = self.camera.projection

        for obj in objects:
            uview = obj.uniforms.view

            model_view = view * obj.model
            model_view_projection = projection * model_view
            model_transpose = obj.model.clone().invert().transpose()

            uview.mvp = model_view_projection.data
            uview.model = obj.model.data
            uview.normal = model_transpose.data
            
        self.scene.update_objects(*objects)

    def handle_keypress(self, event, data):
        if data.key in evt.NumKeys:
            self.app.switch_scene(data)
            return

    def handle_mouse(self, event, event_data):
        if self.camera_view(event, event_data):
            self.update_view()
            self.update_objects()

    def _setup_assets(self):
        scene = self.scene

        self.objects = ()
        self.shaders = ()
