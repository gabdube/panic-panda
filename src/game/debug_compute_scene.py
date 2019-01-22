from engine import Scene, Shader, Compute, Mesh, MeshPrefab, Image, ImageLayout, Sampler, GameObject, CombinedImageSampler
from engine import DeviceCommandList, DeviceCommand, DEFAULT_IMAGE_USAGE
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

        self.heightmap_seed = (1, 1)
        self.heightmap_size = (256, 256)
        self.compute_local_size = self._compute_local_size()

        self.compute_heightmap = None
        self.heightmap_texture = None
        self.heightmap_sampler = None
        self.heightmap_preview = None

        # Camera
        width, height = engine.window.dimensions()
        self.camera = cam = Camera(45, width, height)
        self.camera_view = LookAtView(cam, position = [0,0,-1.9], bounds_zoom=(-3.0, -0.2))

        # Assets
        self._setup_assets()

        # Callbacks
        s.on_initialized = self.init_scene
        s.on_window_resized = self.update_perspective
        s.on_key_pressed = self.handle_keypress
        s.on_mouse_move = s.on_mouse_click = s.on_mouse_scroll = self.handle_mouse

    def init_scene(self):
        engine = self.engine

        w, h = self.heightmap_size
        local_x, local_y = self.compute_local_size
        group_x, group_y = w // local_x, h // local_y

        engine.compute(
            self.scene,
            self.compute_heightmap,
            group = (group_x, group_y, 1),
            sync = True,
            after = DeviceCommandList(
                DeviceCommand.update_image_layout(self.compute_heightmap.id, ImageLayout.ShaderRead)
            ),
            callback = self.show_heightmap
        )

        self.update_objects()

    def show_heightmap(self):
        heightmap_i = self.heightmap_texture
        heightmap_preview_o = self.heightmap_preview

        heightmap_preview_o.uniforms.color_texture = CombinedImageSampler(image_id=heightmap_i.id, view_name="default", sampler_id=self.heightmap_sampler.id)
        self.scene.update_objects(heightmap_preview_o)

    def update_perspective(self, event, data):
        width, height = data
        self.camera.update_perspective(60, width, height)
        self.update_objects()

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
            self.update_objects()

    def _compute_local_size(self):
        # Allocate as much workgroup for invoking compute shaders
        #
        # Workgroup limits varies alot by vendors. 
        #
        # AMD leading by allowing (usually) 1024 max invocations with a 1024 max on the x, y, z local work group
        # NVDIA follows with the same 1024 max invocations, but usually limits the z to 64 instead of 1024
        # And then there's INTEL, begin "special", with a max of 896 invocations.
        #
        from math import sqrt
        INVOKE_SIZE = [1, 2, 4, 8, 16, 32]
        
        limits = self.engine.info["limits"]
        max_invoc = limits.max_compute_work_group_invocations
        max_group_size = limits.max_compute_work_group_size[0:3]
        max_group_count = limits.max_compute_work_group_count[0:3]

        invoke_group = int(sqrt(max_invoc))
        if invoke_group in INVOKE_SIZE:
            return invoke_group, invoke_group

        # if `invoke_group` is not a square number, find the nearest going down
        for size in reversed(INVOKE_SIZE):
            if size < invoke_group:
                return size, size

        raise RuntimeError("Failed to find a suitable workgroup invoke count. This will never happens ")

    def _setup_assets(self):
        scene = self.scene
        engine = self.engine

        # Images
        w, h = self.heightmap_size
        heightmap_i = Image.empty(
            name = "HeightmapImage",
            extent=(w, h, 1),
            format=vk.FORMAT_R8G8B8A8_SNORM,
            usage=DEFAULT_IMAGE_USAGE | vk.IMAGE_USAGE_STORAGE_BIT,
            default_view_type=vk.IMAGE_VIEW_TYPE_2D,
            layout=ImageLayout.ShaderWrite
        )

        placeholder_i = Image.empty(
            name = "PlaceholderImage",
            extent=(1,1,1),
            format=vk.FORMAT_R8G8B8A8_SNORM,
            default_view_type=vk.IMAGE_VIEW_TYPE_2D
        )

        # Samplers
        heightmap_sm = Sampler.from_params(
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
        compute_queue = "render"
        if "compute" in engine.queues:
            compute_queue = "compute"

        ch = "compute_heightmap/compute_heightmap"
        local_x, local_y = self.compute_local_size
        compute_heightmap_c = Compute.from_file(f"{ch}.comp.spv", f"{ch}.map.json", name="ComputeHeightmap", queue=compute_queue)
        compute_heightmap_c.set_constant("local_size_x", local_x)
        compute_heightmap_c.set_constant("local_size_y", local_y)
        compute_heightmap_c.uniforms.heightmap = CombinedImageSampler(image_id=heightmap_i.id, view_name="default", sampler_id=heightmap_sm.id)

        # Meshes
        plane_m = Mesh.from_prefab(MeshPrefab.Plane, attributes_map=debug_texture_attributes_map, name="PlaneMesh")
        
        # Game objects
        preview_heightmap_o = GameObject.from_components(shader = debug_texture_s.id, mesh = plane_m.id, name = "ObjTexture")
        preview_heightmap_o.model = Mat4()
        preview_heightmap_o.uniforms.color_texture = CombinedImageSampler(image_id=placeholder_i.id, view_name="default", sampler_id=heightmap_sm.id)

        scene.images.extend(heightmap_i, placeholder_i)
        scene.samplers.extend(heightmap_sm)
        scene.shaders.extend(debug_texture_s)
        scene.computes.extend(compute_heightmap_c)
        scene.meshes.extend(plane_m)
        scene.objects.extend(preview_heightmap_o)

        self.objects = (preview_heightmap_o,)
        self.shaders = ()
        self.compute_heightmap = compute_heightmap_c
        self.heightmap_texture = heightmap_i
        self.heightmap_sampler = heightmap_sm
        self.heightmap_preview = preview_heightmap_o
