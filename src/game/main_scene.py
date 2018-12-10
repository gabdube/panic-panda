from engine import Shader, GameObject, Scene, Sampler, Image, CombinedImageSampler, Mesh, MeshPrefab
from engine.assets import GLBFile, KTXFile
from utils.mat4 import Mat4
from system import events as evt
from math import radians


class MainScene(object):

    def __init__(self, engine):
        width, height = engine.window.dimensions()

        self.engine = engine
        self.scene = s = Scene.empty()
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
        s.on_initialized = self.init_scene
        s.on_window_resized = self.update_perspective
        s.on_mouse_move = self.move_camera
        s.on_mouse_click = self.move_camera

    def init_scene(self):
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
        scene = self.scene

        # Images & Samplers
        brdf_i = Image.from_ktx(KTXFile.open("brdfLUT.ktx"))
        scene.images.append(brdf_i)

        diffuse_env = Image.from_ktx(KTXFile.open("papermill_diffuse.ktx"))
        scene.images.append(diffuse_env)

        sampler = Sampler.from_params()
        scene.samplers.append(sampler)

        # Shaders
        shader1_attributes_map = {"POSITION": "pos", "NORMAL": "norm", "TANGENT": "tangent"}

        shader1 = Shader.from_files("main/main.vert.spv", "main/main.frag.spv", "main/main.map.json")
        shader1.name = "MainShader"
        shader1.uniforms.rstatic = {"light_color": (1,1,1), "light_direction": (0,0,1), "camera_pos": (0,0,5.5)}
        shader1.uniforms.brdf =     CombinedImageSampler(image_id=brdf_i.id, view_name="default", sampler_id=sampler.id)
        shader1.uniforms.diff_env = CombinedImageSampler(image_id=diffuse_env.id, view_name="default", sampler_id=sampler.id)
        scene.shaders.append(shader1)

        # Meshes
        sphere_m = Mesh.from_gltf(GLBFile.open("test_sphere.glb"), "Sphere.001", attributes_map=shader1_attributes_map)
        scene.meshes.append(sphere_m)

        # Objects
        ball_o = GameObject.from_components(shader = shader1.id, mesh = sphere_m.id)
        ball_o.name = "Ball"
        ball_o.model = Mat4.from_translation(1.5, 0, 0)
        ball_o.uniforms.mat = {"color": (0.7, 0.2, 0.2, 1.0), "roughness_metallic": (1.0, 0.1)}
        scene.objects.append(ball_o)

        ball_o2 = GameObject.from_components(shader = shader1.id, mesh = sphere_m.id)
        ball_o2.name = "Ball2"
        ball_o2.model = Mat4.from_translation(-1.5, 0, 0)
        ball_o2.uniforms.mat = {"color": (0.2, 0.7, 0.2, 1.0), "roughness_metallic": (0.2, 1.0)}
        scene.objects.append(ball_o2)

        self.shader = shader1
        self.objects = [ball_o, ball_o2]
        self.scene = scene

        #
        # Debug stuff
        #

        shader2_attributes_map = {"POSITION": "pos", "TEXCOORD_0": "uv"}
        shader2 = Shader.from_files("texture_debug/texture_debug.vert.spv", "texture_debug/texture_debug.frag.spv", "texture_debug/texture_debug.map.json")
        shader2.name = "DebugTexture"
        #scene.shaders.append(shader2)

        array = Image.from_ktx(KTXFile.open("papermill_diffuse2.ktx"))
        array.name = "papermill_diffuse2.ktx"
        #scene.images.append(array)

        plane_m = Mesh.from_prefab(MeshPrefab.Plane, attributes_map=shader2_attributes_map)
        #scene.meshes.append(plane_m)

        plane_o = GameObject.from_components(shader = shader2.id, mesh = plane_m.id)
        plane_o.name = "Debug Plane"
        plane_o.model = Mat4.from_translation(0.0, 0.0, 3.0)
        plane_o.uniforms.color_texture = CombinedImageSampler(image_id=array.id, view_name="default", sampler_id=sampler.id)
        #scene.objects.append(plane_o)

        #self.objects.append(plane_o)
