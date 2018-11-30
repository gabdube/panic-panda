from engine import Shader, GameObject, Scene, Image
from engine import Mesh, TypedArray, TypedArrayFormat as AFmt
from engine.assets import GLBFile, KTXFile
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

        # Global state stuff
        self.mouse_state = { btn: evt.MouseClickState.Up for btn in evt.MouseClickButton }
        self.mouse_state["pos"] = (0,0)
        
        cam_pos = [0,0,-5.5]
        self.camera = { 
            "pos_vec": cam_pos,
            "pos":  Mat4.from_translation(*cam_pos),
            "proj": Mat4.perspective(radians(60), width/height, 0.001, 1000.0)
        }

        # Assets
        self._load_assets()
        
        # Callbacks
        s = self.scene
        s.on_initialized = self.init_scene
        s.on_window_resized = self.update_perspective
        s.on_mouse_move = self.move_camera
        s.on_mouse_click = self.move_camera

    def init_scene(self):
        rstatic = self.shader.uniforms.rstatic
        rstatic.light_color = (1,1,1)
        rstatic.light_direction = (0,0,1)
        rstatic.camera_pos = (0,0, 5.5)

        self.scene.update_shaders(self.shader)
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

            mat = obj.uniforms.mat
            mat.color[::] = obj.mat["color"]
            mat.roughness_metallic[:2] = obj.mat["rm"]

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

    def _load_assets(self):
        scene = Scene.empty()

        shader = Shader.from_files("main/main.vert.spv", "main/main.frag.spv", "main/main.map.json")
        shader.name = "MainShader"
        scene.shaders.append(shader)

        gltf_attributes_map = {"POSITION": "pos", "NORMAL": "norm", "TANGENT": "tangent"}
        sphere_m = Mesh.from_gltf(GLBFile.open("test_sphere.glb"), "Sphere.001", gltf_attributes_map)
        scene.meshes.append(sphere_m)

        brdf_i = Image.from_ktx(KTXFile.open("brdfLUT.ktx"))
        scene.images.append(brdf_i)

        ball_o = GameObject.from_components(shader = shader.id, mesh = sphere_m.id)
        ball_o.name = "Ball"
        ball_o.model = Mat4.from_translation(1.5, 0, 0)
        ball_o.mat = {"color": (0.7, 0.2, 0.2, 1.0), "rm": (1.0, 0.1)}
        scene.objects.append(ball_o)

        ball_o2 = GameObject.from_components(shader = shader.id, mesh = sphere_m.id)
        ball_o2.name = "Ball2"
        ball_o2.model = Mat4.from_translation(-1.5, 0, 0)
        ball_o2.mat = {"color": (0.2, 0.2, 0.7, 1.0), "rm": (0.2, 1.0)}
        scene.objects.append(ball_o2)

        self.shader = shader
        self.objects = (ball_o, ball_o2)
        self.scene = scene

    def _setup_plane(self):
        return Mesh.from_array(
            indices = TypedArray.from_array(fmt=AFmt.UInt16, array=(0, 1, 2,  0, 3, 2)),
            attributes = {
                "pos": TypedArray.from_array(fmt=AFmt.Float32, array=(-0.7, 0.7, 0,  0.7, 0.7, 0,  0.7, -0.7, 0,  -0.7, -0.7, 0))
            }
        )
