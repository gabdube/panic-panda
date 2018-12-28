from engine import Scene, Mesh, Shader, GameObject
from engine.assets import GLBFile
from system import events as evt
from utils import Mat4
from .components import Camera, LookAtView


class DebugNormalsScene(object):

    def __init__(self, app, engine):
        self.app = app
        self.engine = engine
        self.scene = s = Scene.empty()

        # Global state stuff
        self.objects = []
        self.mouse_state = { btn: evt.MouseClickState.Up for btn in evt.MouseClickButton }
        self.mouse_state["pos"] = (0,0)

        # Camera
        width, height = engine.window.dimensions()
        self.camera = cam = Camera(60, width, height)
        self.camera_view = LookAtView(cam, position = [0,0,-2.5], bounds_zoom=(-7.0, -0.2))

        # Assets
        self._setup_assets()

        # Callbacks
        s.on_initialized = self.init_scene
        s.on_window_resized = self.update_perspective
        s.on_key_pressed = self.handle_keypress
        s.on_mouse_move = s.on_mouse_click = s.on_mouse_scroll = self.handle_mouse

    def init_scene(self):
        self.update_objects()

    def update_perspective(self, event, data):
        self.camera.update_perspective(60, data.width, data.height)
        self.update_objects()

    def handle_keypress(self, event, data):
        k = evt.Key
        if data.key in evt.NumKeys:
            self.app.switch_scene(data) 
    
    def handle_mouse(self, event, event_data):
        if self.camera_view(event, event_data):
            self.update_objects()

    def update_objects(self):
        pass

    def _setup_assets(self):
        scene = self.scene

        # Shaders
        shader_normals_map = {"POSITION": "pos", "NORMAL": "normal", "TANGENT": "tangent"}
        shader_normals = Shader.from_files(
            f"debug_normals/debug_normals.vert.spv",  
            f"debug_normals/debug_normals.frag.spv",
            f"debug_normals/debug_normals.map.json",
            name="DebugNormals"
        )

        # Meshes
        sphere_m = Mesh.from_gltf(GLBFile.open("test_sphere.glb"), "Sphere.001", attributes_map=shader_normals_map, name="SphereMesh")

        # Objects
        sphere = GameObject.from_components(shader = shader_normals.id, mesh = sphere_m.id, name = "Sphere")
        sphere.model = Mat4()

        
        scene.meshes.extend(sphere_m)
        scene.objects.extend(sphere)
        self.objects.append(sphere)
