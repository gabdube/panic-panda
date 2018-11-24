from engine import Shader, GameObject, Scene
from engine import Mesh, TypedArray, TypedArrayFormat as AFmt
from engine.assets import GLBFile
from utils.mat4 import Mat4
from math import radians


class MainScene(object):

    def __init__(self, engine):
        self.engine = engine
        self.scene = None

        self.objects = None

        width, height = engine.window.dimensions()
        self.camera = { 
            "pos":  Mat4.from_translation(0,0,-1.5),
            "proj": Mat4.perspective(radians(60), width/height, 0.001, 1000.0)
        }

        self._load_assets()
        self._bind_callbacks()

    def init_objects(self):
        objects = self.objects
        cam = self.camera
        mvp = cam["proj"] * cam["pos"]

        for obj in objects:
            obj.uniforms.View.mvp = mvp.data

        self.scene.update_objects(*objects)

    def update_perspective(self, event, event_data):
        objects = self.objects
        
        width, height = event_data
        mvp = self.camera["proj"] = Mat4.perspective(radians(60), width/height, 0.001, 1000.0)

        for obj in objects:
            obj.uniforms.View.mvp = mvp.data

        self.scene.update_objects(*objects)

    def _load_assets(self):
        scene = Scene.empty()

        shader = Shader.from_files("main/main.vert.spv", "main/main.frag.spv", "main/main.map.json")
        shader_attributes_map = {"POSITION": "inPos",}
        scene.shaders.append(shader)

        sphere_m = Mesh.from_gltf(GLBFile.open("test_sphere.glb"), "Sphere.001", shader_attributes_map)
        scene.meshes.append(sphere_m)

        plane_m = Mesh.from_array(
            indices = TypedArray.from_array(fmt=AFmt.UInt16, array=(0, 1, 2,  0, 3, 2)),
            attributes = {
                "inPos": TypedArray.from_array(fmt=AFmt.Float32, array=(-0.7, 0.7, 0,  0.7, 0.7, 0,  0.7, -0.7, 0,  -0.7, -0.7, 0))
            }
        )
        scene.meshes.append(plane_m)

        plane_o = GameObject.from_components(shader = shader.id, mesh = plane_m.id)
        scene.objects.append(plane_o)

        self.objects = (plane_o,)
        self.scene = scene

    def _bind_callbacks(self):
        s = self.scene
        s.on_initialized = self.init_objects
        s.on_window_resized = self.update_perspective
