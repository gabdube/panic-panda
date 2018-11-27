from engine import Shader, GameObject, Scene
from engine import Mesh, TypedArray, TypedArrayFormat as AFmt
from engine.assets import GLBFile
from utils.mat4 import Mat4
from system import events as evt
from math import radians


class MainScene(object):

    def __init__(self, engine):
        width, height = engine.window.dimensions()

        self.engine = engine
        self.scene = None
        self.shader = None
        self.objects = None
        self.mouse_state = { btn: evt.MouseClickState.Up for btn in evt.MouseClickButton }
        self.mouse_state["pos"] = (0,0)
        
        cam_pos = [0,0,-3.5]
        self.camera = { 
            "pos_vec": cam_pos,
            "pos":  Mat4.from_translation(*cam_pos),
            "proj": Mat4.perspective(radians(60), width/height, 0.001, 1000.0)
        }

        self._load_assets()
        
        s = self.scene
        s.on_initialized = self.init_scene
        s.on_window_resized = self.update_perspective
        s.on_mouse_move = self.move_camera
        s.on_mouse_click = self.move_camera

    def init_scene(self):
        rstatic = self.shader.uniforms.rstatic
        rstatic.light_color = (1,1,1,0)
        rstatic.light_direction = (1,1,1,0)
        rstatic.camera_pos = (1,1,1,0)

        self.scene.update_shaders(self.shader)
        self.update_objects()

    def update_objects(self):
        objects = self.objects
        cam = self.camera
        model = Mat4()
        mvp = cam["proj"] * cam["pos"]

        for obj in objects:
            view = obj.uniforms.view
            view.model = model.data
            view.normal = model.data
            view.mvp = mvp.data

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
                self.update_objects()

            ms["pos"] = data

    def _load_assets(self):
        scene = Scene.empty()

        shader = Shader.from_files("main/main.vert.spv", "main/main.frag.spv", "main/main.map.json")
        scene.shaders.append(shader)

        gltf_attributes_map = {"POSITION": "pos", "NORMAL": "norm", "TANGENT": "tangent"}
        sphere_m = Mesh.from_gltf(GLBFile.open("test_sphere.glb"), "Sphere.001", gltf_attributes_map)
        scene.meshes.append(sphere_m)

        plane_o = GameObject.from_components(shader = shader.id, mesh = sphere_m.id)
        scene.objects.append(plane_o)

        self.shader = shader
        self.objects = (plane_o,)
        self.scene = scene

    def _setup_plane(self):
        return Mesh.from_array(
            indices = TypedArray.from_array(fmt=AFmt.UInt16, array=(0, 1, 2,  0, 3, 2)),
            attributes = {
                "pos": TypedArray.from_array(fmt=AFmt.Float32, array=(-0.7, 0.7, 0,  0.7, 0.7, 0,  0.7, -0.7, 0,  -0.7, -0.7, 0))
            }
        )
