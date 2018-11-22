from engine import Shader
from engine import Mesh, TypedArray, TypedArrayFormat as DFmt
from engine import GameObject
from engine import Scene
from utils.mat4 import Mat4


class MainScene(object):

    def __init__(self):
        self.scene = None
        self.plane = None
        self._load_assets()
        self._bind_callbacks()

    def init_objects(self):
        self.plane.uniforms.View.mvp[::] = Mat4().data[::]
        self.scene.update_objects(self.plane)

    def _load_assets(self):
        scene = Scene.empty()

        shader = Shader.from_files("main/main.vert.spv", "main/main.frag.spv", "main/main.map.json")
        scene.shaders.append(shader)

        plane_m = Mesh.from_array(
            indices = TypedArray(fmt=DFmt.UInt16, data=(0, 1, 2,  0, 3, 2)),
            attributes = {
                "inPos": TypedArray(fmt=DFmt.Float32, data=(-0.7, 0.7, 0.0,  0.7, 0.7, 0.0,  0.7, -0.7, 0.0,  -0.7, -0.7, 0.0))
            }
        )
        scene.meshes.append(plane_m)

        plane_o = GameObject.from_components(shader = shader.id, mesh = plane_m.id)
        scene.objects.append(plane_o)

        self.plane = plane_o
        self.scene = scene

    def _bind_callbacks(self):
        s = self.scene
        s.on_initialized = self.init_objects
