from engine import Scene
from system import events as evt
from .components import Camera, LookAtView


class DebugAnimationsScene(object):

    def __init__(self, app, engine):
        self.app = app
        self.engine = engine
        self.scene = s = Scene.empty()

        # Camera
        width, height = engine.window.dimensions()
        self.camera = cam = Camera(45, width, height)
        self.camera_view = LookAtView(cam, position = [0,0,-1.9], bounds_zoom=(-3.0, -0.2))

        # Assets
        self._setup_assets()

        # Callbacks
        s.on_initialized = self.init_scene
        s.on_window_resized = self.update_perspective
        s.on_key_pressed = self.handle_keypress
        s.on_mouse_move = s.on_mouse_click = s.on_mouse_scroll = self.handle_mouse

    def init_scene(self):
        pass

    def update_perspective(self, event, data):
        width, height = data
        self.camera.update_perspective(60, width, height)

    def handle_keypress(self, event, data):
        if data.key in evt.NumKeys:
            self.app.switch_scene(data)
            return
    
    def handle_mouse(self, event, event_data):
        if self.camera_view(event, event_data):
            pass

    def _setup_assets(self):
        pass
