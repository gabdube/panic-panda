from engine import Scene, Shader, Mesh, Image, Sampler, GameObject, CombinedImageSampler
from engine.assets import KTXFile, GLTFFile, IMAGE_PATH
from system import events as evt
from utils import Mat4
from vulkan import vk
from .components import Camera, LookAtView
from math import radians, sin, cos


class DebugPBRScene(object):

    def __init__(self, app, engine):
        self.app = app
        self.engine = engine
        self.scene = s = Scene.empty()

        # Global state stuff
        self.shaders = ()
        self.objects = ()
        self.debug = 0

        self.light = {"rot": -95, "pitch": 40}

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
        self.update_light()
        self.update_view()
        
    def update_perspective(self, event, data):
        width, height = data
        self.camera.update_perspective(60, width, height)
        self.update_objects()

    def update_light(self):
        light = self.light
        shader = self.shaders[0]
        render = shader.uniforms.render

        rot, pitch = radians(light["rot"]), radians(light["pitch"])
        render.light_direction[:3] = (
            sin(rot) * cos(pitch),
            sin(pitch),
            cos(rot) * cos(pitch)
        )

        self.scene.update_shaders(shader)

    def update_view(self):
        shader = self.shaders[0]
        render = shader.uniforms.render
        render.camera[:3] = self.camera.position
        self.scene.update_shaders(shader)

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

        # Update debug flags
        k = evt.Keys
        key = data.key
        debug, max_debug = self.debug, 11

        if key is k.Down and debug > 0:
            debug -= 1
        elif key is k.Up and debug+1 < max_debug:
            debug += 1

        helmet_shader = self.shaders[0]
        helmet_shader.uniforms.render.debug[0] = debug

        self.debug = debug
        self.scene.update_shaders(helmet_shader)

    def handle_mouse(self, event, event_data):
        if self.camera_view(event, event_data):
            self.update_view()
            self.update_objects()

    def _setup_assets(self):
        scene = self.scene

        # Images
        helmet_f = KTXFile.open("damaged_helmet.ktx")
        if __debug__:
            helmet_f = helmet_f[2:3]   # Speed up load time by only keeping a low res mipmap in debug mode
        
        specular_env_f = KTXFile.open("storm/specular_cubemap.ktx")
        irradiance_env_f = KTXFile.open("storm/irr_cubemap.ktx")

        with (IMAGE_PATH/"brdf.bin").open("rb") as f:
            brdf_args = {"format": vk.FORMAT_R16G16_UNORM, "extent": (128, 128, 1), "default_view_type": vk.IMAGE_VIEW_TYPE_2D}
            brdf_f = f.read()

        helmet_i = Image.from_ktx(helmet_f, name="HelmetTextureMaps")
        brdf_i = Image.from_uncompressed(brdf_f, name="BRDF", **brdf_args)
        env_i = Image.from_ktx(specular_env_f, name="CubemapTexture")
        env_irr_i = Image.from_ktx(irradiance_env_f, name="CubemapIrradianceTexture")

        # Sampler
        brdf_s = Sampler.new()
        env_s = Sampler.from_params(max_lod=env_i.mipmaps_levels)
        helmet_s = Sampler.from_params(max_lod=helmet_i.mipmaps_levels)              

        # Shaders
        n = "pbr2/pbr2"
        shader_map = {"POSITION": "pos", "NORMAL": "normal", "TEXCOORD_0": "uv"}
        shader = Shader.from_files(f"{n}.vert.spv", f"{n}.frag.spv", f"{n}.map.json", name="PBRShader")
        
        color_factor = 1.0
        emissive_factor = 1.0
        exposure = 1.5
        gamma = 2.2

        shader.uniforms.render = {
            "light_color": (1.0, 1.0, 1.0),
            "env_lod": (0, env_i.mipmaps_levels),
            "factors": (
                color_factor,
                emissive_factor,
                exposure,
                gamma
            )
        }

        shader.uniforms.brdf = CombinedImageSampler(image_id=brdf_i.id, view_name="default", sampler_id=brdf_s.id)
        shader.uniforms.env_specular = CombinedImageSampler(image_id=env_i.id, view_name="default", sampler_id=env_s.id)
        shader.uniforms.env_irradiance = CombinedImageSampler(image_id=env_irr_i.id, view_name="default", sampler_id=brdf_s.id)

        # Meshes
        helmet_m = Mesh.from_gltf(GLTFFile.open("DamagedHelmet.gltf"), "HelmetMesh", attributes_map=shader_map, name="HelmetMesh")

        # Objects
        helmet = GameObject.new(shader = shader.id, mesh = helmet_m.id, name = "Helmet")
        helmet.model = Mat4().from_rotation(radians(90), (1, 0, 0))
        helmet.uniforms.texture_maps = CombinedImageSampler(image_id=helmet_i.id, view_name="default", sampler_id=helmet_s.id)

        # Packing
        scene.images.extend(helmet_i, brdf_i, env_i, env_irr_i)
        scene.samplers.extend(helmet_s, brdf_s, env_s)
        scene.shaders.extend(shader)
        scene.meshes.extend(helmet_m)
        scene.objects.extend(helmet)

        self.objects = (helmet,)
        self.shaders = (shader,)
