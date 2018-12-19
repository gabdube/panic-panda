from engine import Scene, Shader, Image, Sampler, CombinedImageSampler, Mesh, GameObject
from engine.assets import GLBFile, KTXFile
from system import events as evt
from utils import Mat4
from .components import Camera, LookAtView
from math import radians


class DebugSkeletonScene(object):

    def __init__(self, app, engine):
        self.app = app
        self.engine = engine
        self.scene = s = Scene.empty()
        
        self.shader = None
        self.bunny_obj = None

        # Component
        width, height = engine.window.dimensions()
        self.camera = cam = Camera(60, width, height)
        self.camera_view = LookAtView(cam, position = [0,0,1.5])

        # Assets
        self._setup_assets()

        # Callbacks
        s.on_initialized = self.init_scene
        s.on_window_resized = self.update_perspective
        s.on_key_pressed = self.handle_keypress
        s.on_mouse_move = s.on_mouse_click = s.on_mouse_scroll = self.handle_mouse

    def init_scene(self):
        self.update_camera()
        self.update_object()

    def update_camera(self):
        shader = self.shader
        rstatic = shader.uniforms.rstatic

        rstatic.camera_pos[:3] = self.camera.position
        self.scene.update_shaders(shader)

    def update_object(self):
        bunny = self.bunny_obj
        bunny_view = bunny.uniforms.view
        bunny_view.mvp[::] = self.camera.view_projection * bunny.model
        self.scene.update_objects(bunny)

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
        cam = self.camera

        # Images
        brdf = Image.from_ktx(KTXFile.open("brdfLUT.ktx"), name="BrdfTexture")
        diffuse_env = Image.from_ktx(KTXFile.open("papermill_diffuse.ktx"), name="DiffuseTexture")

        # Samplers
        sampler = Sampler.new(name="BunnySampler")
        
        # Shaders
        main_shader_attributes_map = {"POSITION": "pos", "NORMAL": "norm", "TANGENT": "tangent"}

        self.shader = main_shader = Shader.from_files("main/main.vert.spv", "main/main.frag.spv", "main/main.map.json", name="MainShader")
        main_shader.uniforms.rstatic = {"light_color": (1,1,1), "light_direction": (-0.5,1,0.4), "camera_pos": (0,0,0)}
        main_shader.uniforms.brdf =     CombinedImageSampler(image_id=brdf.id, view_name="default", sampler_id=sampler.id)
        main_shader.uniforms.diff_env = CombinedImageSampler(image_id=diffuse_env.id, view_name="default", sampler_id=sampler.id)

        # Meshes
        bunny_mesh = Mesh.from_gltf(GLBFile.open("bunny.glb"), "BunnyMesh", attributes_map=main_shader_attributes_map, name="BunnyMesh")

        # Game objects
        self.bunny_obj = bunny = GameObject.from_components(shader = main_shader.id, mesh = bunny_mesh.id, name = "Bunny")
        bunny.model = model = Mat4.from_rotation(radians(180), (0,0,1))
        bunny.uniforms.mat = {"color": (0.7, 0.7, 0.7, 1.0), "roughness_metallic": (0.2, 1.0)}
        bunny.uniforms.view = {"normal": Mat4().data, "model": model}

        # Add the objects to the scene
        scene.images.extend(brdf, diffuse_env)
        scene.samplers.extend(sampler)
        scene.meshes.extend(bunny_mesh)
        scene.shaders.extend(main_shader)
        scene.objects.extend(bunny)
