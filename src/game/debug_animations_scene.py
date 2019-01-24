from engine import Scene, Image, Sampler, Shader, CombinedImageSampler, Mesh, GameObject
from engine.assets import KTXFile, GLBFile, IMAGE_PATH
from system import events as evt
from utils import Mat4
from vulkan import vk
from .components import Camera, LookAtView
from math import radians


class DebugAnimationsScene(object):

    def __init__(self, app, engine):
        self.app = app
        self.engine = engine
        self.scene = s = Scene.empty()

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
        pass

    def update_perspective(self, event, data):
        width, height = data
        self.camera.update_perspective(60, width, height)

    def handle_keypress(self, event, data):
        if data.key in evt.NumKeys:
            self.app.switch_scene(data)
            return
    
    def handle_mouse(self, event, event_data):
        if self.camera_view(event, event_data):
            pass

    def _setup_assets(self):
        scene = self.scene

        # Images
        specular_env_f = KTXFile.open("storm/specular_cubemap.ktx")
        irradiance_env_f = KTXFile.open("storm/irr_cubemap.ktx")

        with (IMAGE_PATH/"brdf.bin").open("rb") as f:
            brdf_args = {"format": vk.FORMAT_R16G16_UNORM, "extent": (128, 128, 1), "default_view_type": vk.IMAGE_VIEW_TYPE_2D}
            brdf_f = f.read()

        brdf_i = Image.from_uncompressed(brdf_f, name="BRDF", **brdf_args)
        env_i = Image.from_ktx(specular_env_f, name="CubemapTexture")
        env_irr_i = Image.from_ktx(irradiance_env_f, name="CubemapIrradianceTexture")

        # Sampler
        brdf_s = Sampler.new()
        env_s = Sampler.from_params(max_lod=env_i.mipmaps_levels)

        # Shaders
        pbr_s = self._setup_pbr()
        pbr_s.uniforms.render["env_lod"] = (0, env_i.mipmaps_levels)
        pbr_s.uniforms.brdf = CombinedImageSampler(image_id=brdf_i.id, view_name="default", sampler_id=brdf_s.id)
        pbr_s.uniforms.env_specular = CombinedImageSampler(image_id=env_i.id, view_name="default", sampler_id=env_s.id)
        pbr_s.uniforms.env_irradiance = CombinedImageSampler(image_id=env_irr_i.id, view_name="default", sampler_id=brdf_s.id)
        
        # Meshes
        bunny_m = Mesh.from_gltf(GLBFile.open("bunny.glb"), "BunnyMesh", attributes_map=pbr_map, name="BunnyMesh")

        # Objects   
        bunny_o = GameObject.from_components(shader = pbr_s.id, mesh = bunny_m.id, name = "Bunny")
        bunny_o.model = Mat4().from_rotation(radians(90), (1, 0, 0))
        #bunny_o.uniforms.texture_maps = CombinedImageSampler(image_id=helmet_i.id, view_name="default", sampler_id=helmet_s.id)

        # Packing
        scene.images.extend(brdf_i, env_i, env_irr_i)
        scene.samplers.extend(brdf_s, env_s)
        scene.shaders.extend(pbr_s)
        scene.meshes.extend(bunny_m)
        scene.objects.extend(bunny_o)

    def _setup_pbr(self):
        name = "pbr/pbr"
        pbr_map = {"POSITION": "pos", "NORMAL": "normal", "TEXCOORD_0": "uv"}
        pbr_s = Shader.from_files(f"{name}.vert.spv", f"{name}.frag.spv", f"{name}.map.json", name="PBRShader")
        
        color_factor = 1.0
        emissive_factor = 1.0
        exposure = 1.5
        gamma = 2.2

        pbr_s.uniforms.render = {
            "light_color": (1.0, 1.0, 1.0),
            "factors": (
                color_factor,
                emissive_factor,
                exposure,
                gamma
            )
        }
        
        return pbr_s
