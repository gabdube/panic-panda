from engine import Scene, Shader, Image, Sampler, CombinedImageSampler
from engine.assets import GLBFile, KTXFile
from system import events as evt


class DebugSkeletonScene(object):

    def __init__(self, app, engine):
        self.app = app
        self.engine = engine
        self.scene = s = Scene.empty()

        self.objects = []

        # Assets
        self._setup_assets()

        # Callbacks
        s.on_key_pressed = self.handle_keypress

    def handle_keypress(self, event, data):
        k = evt.Keys
        if data.key in evt.NumKeys:
            self.app.switch_scene(data) 

    def _setup_assets(self):
        scene = self.scene

        # Images
        brdf = Image.from_ktx(KTXFile.open("brdfLUT.ktx"), name="BrdfTexture")
        diffuse_env = Image.from_ktx(KTXFile.open("papermill_diffuse.ktx"), name="DiffuseTexture")

        # Samplers
        sampler = Sampler.new()
        
        # Shaders
        main_shader_attributes_map = {"POSITION": "pos", "NORMAL": "norm", "TANGENT": "tangent"}

        main_shader = Shader.from_files("main/main.vert.spv", "main/main.frag.spv", "main/main.map.json", name="MainShader")
        main_shader.uniforms.rstatic = {"light_color": (1,1,1), "light_direction": (0,0,1), "camera_pos": (0,0,5.5)}
        main_shader.uniforms.brdf =     CombinedImageSampler(image_id=brdf.id, view_name="default", sampler_id=sampler.id)
        main_shader.uniforms.diff_env = CombinedImageSampler(image_id=diffuse_env.id, view_name="default", sampler_id=sampler.id)
        
        # Add the objects to the scene
        scene.images.extend(brdf, diffuse_env)
        scene.samplers.extend(sampler)
        scene.shaders.extend(main_shader)
