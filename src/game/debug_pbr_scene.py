from engine import Shader, GameObject, Scene, Sampler, Image, CombinedImageSampler, Mesh, MeshPrefab
from engine.assets import GLBFile, KTXFile
from system import events as evt
from utils import Mat4
from vulkan import vk
from .components import Camera, LookAtView
from math import radians


class DebugPBRScene(object):

    def __init__(self, app, engine):
        self.app = app
        self.engine = engine
        self.scene = s = Scene.empty()
        
        # Global state stuff
        self.mouse_state = { btn: evt.MouseClickState.Up for btn in evt.MouseClickButton }
        self.mouse_state["pos"] = (0,0)

        # Camera
        width, height = engine.window.dimensions()
        self.camera = cam = Camera(60, width, height)
        self.camera_view = LookAtView(cam, position = [0,0,3.5], bounds_zoom=(0.2, 7.0))

        # Assets
        self.pbr_shader = None
        self.render_object = None
        self._setup_assets()

        # Callbacks
        s.on_initialized = self.init_scene
        s.on_window_resized = self.update_perspective
        s.on_key_pressed = self.handle_keypress
        s.on_mouse_move = s.on_mouse_click = s.on_mouse_scroll = self.handle_mouse

    def init_scene(self):
        self.update_camera()
        self.update_object()

    def update_camera(self):
        pass

    def update_object(self):
        pass

    def update_perspective(self, event, data):
        self.camera.update_perspective(60, data.width, data.height)
        self.update_object()
    
    def handle_keypress(self, event, data):
        k = evt.Keys
        if data.key in evt.NumKeys:
            self.app.switch_scene(data) 

    def handle_mouse(self, event, event_data):
        if self.camera_view(event, event_data):
            self.update_camera()
            self.update_object()

    def _setup_assets(self):
        pass