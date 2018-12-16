from engine import Shader, GameObject, Scene, Sampler, Image, CombinedImageSampler, Mesh, MeshPrefab
from engine.assets import GLBFile, KTXFile
from utils.mat4 import Mat4
from system import events as evt
from math import radians


class MainScene(object):

    def __init__(self, app, engine):
        self.app = app
        self.engine = engine
        self.scene = s = Scene.empty()
        self.shader = None
        self.objects = []

        # Global state stuff
        self.mouse_state = { btn: evt.MouseClickState.Up for btn in evt.MouseClickButton }
        self.mouse_state["pos"] = (0,0)
        
        width, height = engine.window.dimensions()
        cam_pos = [0,0,-5.5]
        self.camera = { 
            "pos_vec": cam_pos,
            "pos":  Mat4.from_translation(*cam_pos),
            "proj": Mat4.perspective(radians(60), width/height, 0.001, 1000.0)
        }

        # Callbacks
        s.on_initialized = self.init_scene
        s.on_window_resized = self.update_perspective
        s.on_mouse_move = self.move_camera
        s.on_mouse_click = self.move_camera
        s.on_key_pressed = self.handle_keypress

    def init_scene(self):
        self.update_objects()

    def update_objects(self):
        objects = self.objects
        cam = self.camera
        mvp = cam["proj"] * cam["pos"]

        for obj in objects:
            view = obj.uniforms.view
            view.model = obj.model.data
            view.normal = obj.model.data
            view.mvp = (mvp * obj.model).data

        self.scene.update_objects(*objects)

    def update_perspective(self, event, data):
        objects = self.objects
        cam = self.camera
        
        width, height = data
        cam["proj"] = Mat4.perspective(radians(60), width/height, 0.001, 1000.0)

        self.update_objects()

    def move_camera(self, event, data):
        ms = self.mouse_state
        if event is evt.MouseClick:
            ms[data.button] = data.state
        elif event is evt.MouseMove:
            x1, y1 = data
            x2, y2 = ms["pos"]
            right, left, *_ = evt.MouseClickButton
            down = evt.MouseClickState.Down
            cam = self.camera

            if ms[left] is down:
                cam["pos_vec"][2] += (y2 - y1) * -0.01
                cam["pos"] = Mat4.from_translation(*cam["pos_vec"])

                rstatic = self.shader.uniforms.rstatic
                rstatic.camera_pos[2] = abs(cam["pos_vec"][2])
                self.scene.update_shaders(self.shader)

                self.update_objects()

            ms["pos"] = data

    def handle_keypress(self, event, data):
        k = evt.Keys
        if data.key in evt.NumKeys:
            self.app.switch_scene(data) 

