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
        self.scene = Scene.empty()
        
        # Global state stuff
        self.mouse_state = { btn: evt.MouseClickState.Up for btn in evt.MouseClickButton }
        self.mouse_state["pos"] = (0,0)

        # Camera
        width, height = engine.window.dimensions()
        self.camera = cam = Camera(60, width, height)
        self.camera_view = LookAtView(cam, position = [0,0,3.5], bounds_zoom=(1.6, 7.0))

        # Assets
        self.pbr_shader = None
        self.render_object = None
        self._setup_assets()

        # Callbacks
        s = self.scene
        s.on_initialized = self.init_scene
        s.on_window_resized = self.update_perspective
        s.on_key_pressed = self.handle_keypress
        s.on_mouse_move = s.on_mouse_click = s.on_mouse_scroll = self.handle_mouse

    def init_scene(self):
        self.update_camera()
        self.update_object()

        self.scene.update_shaders(self.pbr_shader)

    def update_camera(self):
        pass

    def update_object(self):
        cam = self.camera
        helmet = self.render_object
        view = helmet.uniforms.view

        view.model_view = (cam.view * helmet.model).data
        view.projection = cam.projection.data
        view.model_view_normal = Mat4().data
        
        self.scene.update_objects(helmet)

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
        scene = self.scene

        helmet_maps = Image.from_ktx(KTXFile.open("damaged_helmet.ktx"), name="HelmetTextureMaps")
        if __debug__:
            helmet_maps = helmet_maps[3:]   # Cut the first two mipmap levels in debug mode to speed up load times

        helmet_sampler = Sampler.new(max_lod=helmet_maps.mipmaps_levels)

        pbr_attributes_map = {"POSITION": "pos", "NORMAL": "normal", "TANGENT": "tangent", "TEXCOORD_0": "uv"}
        pbr = Shader.from_files(f"pbr/pbr.vert.spv",  f"pbr/pbr.frag.spv", f"pbr/pbr.map.json", name="PBR")
        pbr.uniforms.render = {
            "base_color_factor": (1.0, 1.0, 1.0, 0.0),
            "emissive_factor": (1.0, 1.0, 1.0, 1.0),
            "factors": (1.0, 1.0, 1.0, 1.0),
            "env_spherical_harmonics": (0.0, 0.0, 0.0, 0.0)
        }

        helmet_mesh = Mesh.from_gltf(GLBFile.open("damaged_helmet.glb"), "HelmetMesh", attributes_map=pbr_attributes_map, name="HelmetMesh")

        helmet = GameObject.from_components(shader = pbr.id, mesh = helmet_mesh.id, name = "Helmet")
        helmet.model = Mat4()
        helmet.uniforms.texture_maps = CombinedImageSampler(image_id=helmet_maps.id, view_name="default", sampler_id=helmet_sampler.id)

        scene.images.extend(helmet_maps)
        scene.samplers.extend(helmet_sampler)
        scene.shaders.extend(pbr)
        scene.meshes.extend(helmet_mesh)
        scene.objects.extend(helmet)

        self.pbr_shader = pbr
        self.render_object = helmet
