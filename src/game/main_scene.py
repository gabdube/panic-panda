from engine import Shader
from engine import Mesh, DataArray, DataArrayFormat as DFmt
from engine import GameObject
from engine import Scene


class MainScene(object):

    def __init__(self):
        self.scene = None
        self._load_assets()
        self._bind_callbacks()

    def on_window_resized(self, width, height):
        for obj in self.scene.objects:
            obj.uniforms.mvp = None

    def _load_assets(self):
        scene = Scene.empty()

        shader = Shader.from_files("main/main.vert.spv", "main/main.frag.spv", "main/main.map.json")
        scene.shaders.append(shader)

        plane_m = Mesh.from_array(
            indices = DataArray(fmt=DFmt.UInt16, data=()),
            attributes = {
                "positions": DataArray(fmt=DFmt.Float32, data=())
            }
        )
        scene.meshes.append(plane_m)

        plane_o = GameObject.from_components(shader = shader.id, mesh = plane_m.id)
        scene.objects.append(plane_o)

        self.scene = scene

    def _bind_callbacks(self):
        s = self.scene
        s.on_display_resized = self.on_window_resized

