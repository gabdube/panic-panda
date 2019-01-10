from engine import Scene, Shader, Compute, Mesh, MeshPrefab, Image, Sampler, GameObject, CombinedImageSampler
from engine.assets import KTXFile, GLTFFile, IMAGE_PATH
from system import events as evt
from utils import Mat4
from vulkan import vk
from .components import Camera, LookAtView
from math import radians, sin, cos


class DebugComputeScene(object):

    def __init__(self, app, engine):
        self.app = app
        self.engine = engine
        self.scene = s = Scene.empty()

        # Global state stuff
        self.shaders = ()
        self.objects = ()
        self.compute_heightmap = None

        # Camera
        width, height = engine.window.dimensions()
        self.camera = cam = Camera(45, width, height)
        self.camera_view = LookAtView(cam, position = [0,0,-3.5], bounds_zoom=(-7.0, -0.2))

        # Assets
        self._setup_assets()

        # Callbacks
        s.on_initialized = self.init_scene
        s.on_window_resized = self.update_perspective
        s.on_key_pressed = self.handle_keypress
        s.on_mouse_move = s.on_mouse_click = s.on_mouse_scroll = self.handle_mouse

    def init_scene(self):
        self.update_objects()
        self.update_view()
        
    def update_perspective(self, event, data):
        width, height = data
        self.camera.update_perspective(60, width, height)
        self.update_objects()

    def update_view(self):
        return

    def update_objects(self):
        objects = self.objects
        view = self.camera.view
        projection = self.camera.projection

        for obj in objects:
            uview = obj.uniforms.view

            model_view = view * obj.model
            model_view_projection = projection * model_view
            model_transpose = obj.model.clone().invert().transpose()

            uview.mvp = model_view_projection.data
            uview.model = obj.model.data
            uview.normal = model_transpose.data
            
        self.scene.update_objects(*objects)

    def handle_keypress(self, event, data):
        if data.key in evt.NumKeys:
            self.app.switch_scene(data)
            return

    def handle_mouse(self, event, event_data):
        if self.camera_view(event, event_data):
            self.update_view()
            self.update_objects()

    def _setup_assets(self):
        scene = self.scene

        # Images
        heightmap_i = Image.empty(
            extent=(1024, 1024, 1),
            format=vk.FORMAT_R32_SFLOAT,
            default_view_type=vk.IMAGE_VIEW_TYPE_2D
        )

        # Samplers
        heightmap_s = Sampler.from_params(
            address_mode_V=vk.SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
            address_mode_U=vk.SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
            mag_filter=vk.FILTER_NEAREST,
            min_filter=vk.FILTER_NEAREST
        )

        # Shaders
        dt = "debug_texture/debug_texture"
        debug_texture_attributes_map = {"POSITION": "pos", "TEXCOORD_0": "uv"}
        debug_texture_s = Shader.from_files(f"{dt}.vert.spv",  f"{dt}.frag.spv", f"{dt}.map.json", name="DebugTexture")

        # Compute shaders
        ch = "compute_heightmap/compute_heightmap"
        compute_heightmap_c = Compute.from_file(f"{ch}.comp", f"{ch}.map.json", name="ComputeHeightmap")

        # Meshes
        plane_m = Mesh.from_prefab(MeshPrefab.Plane, attributes_map=debug_texture_attributes_map, name="PlaneMesh")
        
        # Game objects
        preview_heightmap_o = GameObject.from_components(shader = debug_texture_s.id, mesh = plane_m.id, name = "ObjTexture")
        preview_heightmap_o.model = Mat4()
        preview_heightmap_o.uniforms.color_texture = CombinedImageSampler(image_id=heightmap_i.id, view_name="default", sampler_id=heightmap_s.id)

        scene.images.extend(heightmap_i)
        scene.samplers.extend(heightmap_s)
        scene.shaders.extend(debug_texture_s)
        scene.computes.extend(compute_heightmap_c)
        scene.meshes.extend(plane_m)
        scene.objects.extend(preview_heightmap_o)

        self.objects = (preview_heightmap_o,)
        self.shaders = ()
        self.compute_heightmap = compute_heightmap_c
