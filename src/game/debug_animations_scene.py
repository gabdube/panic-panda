from engine import Scene, Image, Sampler, Shader, CombinedImageSampler, Mesh, GameObject, Animation, AnimationPlayback
from engine.assets import KTXFile, GLBFile, IMAGE_PATH
from system import events as evt
from utils import Mat4
from vulkan import vk
from .components import Camera, LookAtView
from math import radians, sin, cos


class DebugAnimationsScene(object):

    def __init__(self, app, engine):
        self.app = app
        self.engine = engine
        self.scene = s = Scene.empty()

        # Global state
        self.objects = []
        self.animations = {}
        self.light = {"rot": -95, "pitch": 40}
        self.debug = 0

        # Camera
        width, height = engine.window.dimensions()
        self.camera = cam = Camera(45, width, height)
        self.camera_view = LookAtView(cam, position = [0,0.25,-3.2], bounds_zoom=(-5.0, -1.2), mod_translate=0.0035)

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
        self.play_animations()
       
    def play_animations(self):
        inner_box_obj = self.objects[0]
        rotate, translate = self.animations['rotate'], self.animations['translate']

        rotate.play(inner_box_obj.id, playback=AnimationPlayback.Once)
        translate.play(inner_box_obj.id, playback=AnimationPlayback.Once)

        self.scene.update_animations(rotate, translate)

    def update_light(self):
        light = self.light
        for shader in self.shaders:
            render = shader.uniforms.render

            rot, pitch = radians(light["rot"]), radians(light["pitch"])
            render.light_direction[:3] = (
                sin(rot) * cos(pitch),
                sin(pitch),
                cos(rot) * cos(pitch)
            )

        self.scene.update_shaders(*self.shaders)

    def update_view(self):
        for shader in self.shaders:
            render = shader.uniforms.render
            render.camera[:3] = self.camera.position

        self.scene.update_shaders(*self.shaders)

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

    def update_perspective(self, event, data):
        width, height = data
        self.camera.update_perspective(60, width, height)
        self.update_objects()

    def handle_keypress(self, event, data):
        if data.key in evt.NumKeys:
            self.app.switch_scene(data)
            return

        self._update_debug_flag(data)
    
    def handle_mouse(self, event, event_data):
        if self.camera_view(event, event_data):
            self.update_view()
            self.update_objects()

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
        brdf_sm = Sampler.new()
        env_sm = Sampler.from_params(max_lod=env_i.mipmaps_levels)

        # Shaders
        bunny_pbr_s = self._setup_pbr(
            shader_name = "BunnyShaderPBR",
            constants = {
                "use_diffuse": True,
                "diffuse_index": 0,
                "use_ibl": True,
                "debug": True
            },
            uniforms = {
                "render": {"env_lod": (0, env_i.mipmaps_levels)},
                "brdf": CombinedImageSampler(image_id=brdf_i.id, view_name="default", sampler_id=brdf_sm.id),
                "env_specular": CombinedImageSampler(image_id=env_i.id, view_name="default", sampler_id=env_sm.id),
                "env_irradiance": CombinedImageSampler(image_id=env_irr_i.id, view_name="default", sampler_id=brdf_sm.id)
            }
        )

        box_pbr_s = self._setup_pbr(
            shader_name = "BoxShaderPBR",
            constants = {
                "use_diffuse": False,
                "use_ibl": True,
                "debug": True
            },
            uniforms = {
                "render": {"env_lod": (0, env_i.mipmaps_levels)},
                "brdf": CombinedImageSampler(image_id=brdf_i.id, view_name="default", sampler_id=brdf_sm.id),
                "env_specular": CombinedImageSampler(image_id=env_i.id, view_name="default", sampler_id=env_sm.id),
                "env_irradiance": CombinedImageSampler(image_id=env_irr_i.id, view_name="default", sampler_id=brdf_sm.id)
            },
            attr_filter = [
                "uv"
            ]
        )
        
        # Objects
        # self._load_bunny_mesh(scene, bunny_pbr_s)
        self._load_box_animated(scene, box_pbr_s)

        # Packing
        scene.images.extend(brdf_i, env_i, env_irr_i)
        scene.samplers.extend(brdf_sm, env_sm)
        scene.shaders.extend(bunny_pbr_s, box_pbr_s)

        self.shaders = (bunny_pbr_s, box_pbr_s)

    def _setup_pbr(self, constants, uniforms, shader_name, attr_filter=()):
        name = "pbr/pbr"
        pbr_map = {"POSITION": "pos", "NORMAL": "normal", "TEXCOORD_0": "uv"}
        pbr_s = Shader.from_files(f"{name}.vert.spv", f"{name}.frag.spv", f"{name}.map.json", name=shader_name)

        # Remove certain attributes that won't be used by the linked meshes
        for attr in attr_filter:
            pbr_s.toggle_attribute(attr, False)

        render = {
            "light_color": (1.0, 1.0, 1.0),
            "factors": (
                1.3,   # Color factor
                1.0,   # Emissive factor
                1.5,   # Exposure
                2.2    # Gamma
            )
        }

        if "render" in uniforms:
            render.update(uniforms["render"])
            uniforms["render"] = render

        for uniform_name, uniform_value in uniforms.items():
            setattr(pbr_s.uniforms, uniform_name, uniform_value)

        for constant_name, constant_value in constants.items():
            pbr_s.set_constant(constant_name, constant_value)
        
        pbr_s.attributes_map = pbr_map

        return pbr_s

    def _load_bunny_mesh(self, scene, shader):
        bunny_f = KTXFile.open("bunny.ktx")
        if __debug__:
            bunny_f = bunny_f[1:2]   # Speed up load time by only keeping a low res mipmap in debug mode

        # Images
        bunny_i = Image.from_ktx(bunny_f, name="BunnyTexture")
        
        # Samplers
        bunny_sm = Sampler.from_params(max_lod=bunny_i.mipmaps_levels)

        # Meshes
        bunny_m = Mesh.from_gltf(GLBFile.open("bunny.glb"), "BunnyMesh", attributes_map=shader.attributes_map, name="BunnyMesh")

        # Objects
        bunny_o = GameObject.new(shader = shader.id, mesh = bunny_m.id, name = "Bunny")
        bunny_o.model = Mat4().from_rotation(radians(90), (1, 0, 0))
        bunny_o.uniforms.texture_maps = CombinedImageSampler(image_id=bunny_i.id, view_name="default", sampler_id=bunny_sm.id)
        bunny_o.uniforms.base_material = {"metallic_roughness": (0.0, 0.0)}

        # Packing
        scene.images.extend(bunny_i)
        scene.samplers.extend(bunny_sm)
        scene.meshes.extend(bunny_m)
        scene.objects.extend(bunny_o)

        self.objects.append(bunny_o)

    def _load_box_animated(self, scene, shader):
        animated_f = GLBFile.open("BoxAnimated.glb")

        # Images
        placeholder_i = Image.empty(
            name="PlaceholderImage",
            extent=(1,1,1),
            format=vk.FORMAT_R8G8B8A8_SNORM,
            default_view_type=vk.IMAGE_VIEW_TYPE_2D_ARRAY
        )

        # Samplers
        sm = Sampler.new()

        # Meshes
        inner_m = Mesh.from_gltf(animated_f, "inner_box", attributes_map=shader.attributes_map, name="InnerBox")
        outer_m = Mesh.from_gltf(animated_f, "outer_box", attributes_map=shader.attributes_map, name="OuterBox")

        # Animations
        rotate_inner_a = Animation.from_gltf(animated_f, 0)
        translate_inner_a = Animation.from_gltf(animated_f, 1)
        inner_animations = {"rotate": rotate_inner_a, "translate": translate_inner_a}

        # Objects
        inner_o = GameObject.new(shader=shader.id, mesh=inner_m.id, name="InnerBox")
        inner_o.model = Mat4()
        inner_o.uniforms.texture_maps = CombinedImageSampler(image_id=placeholder_i.id, view_name="default", sampler_id=sm.id)
        inner_o.uniforms.base_material = {"color": (1.0, 1.0, 1.0, 1.0),  "metallic_roughness": (0.0, 1.0)}

        outer_o = GameObject.new(shader=shader.id, mesh=outer_m.id, name="OuterBox")
        outer_o.model = Mat4()
        outer_o.uniforms.texture_maps = CombinedImageSampler(image_id=placeholder_i.id, view_name="default", sampler_id=sm.id)
        outer_o.uniforms.base_material = {"color": (1.0, 0.0, 0.0, 1.0),  "metallic_roughness": (0.0, 1.0)}
        
        scene.images.extend(placeholder_i)
        scene.samplers.extend(sm)
        scene.meshes.extend(inner_m, outer_m)
        scene.animations.extend(rotate_inner_a, translate_inner_a)
        scene.objects.extend(inner_o, outer_o)

        self.objects.extend((inner_o, outer_o))
        self.animations = inner_animations

    def _update_debug_flag(self, data):
        # Update debug flags
        k = evt.Keys
        key = data.key
        debug, max_debug = self.debug, 11

        if key is k.Down and debug > 0:
            debug -= 1
        elif key is k.Up and debug+1 < max_debug:
            debug += 1

        shader = self.shaders[0]
        shader.uniforms.render.debug[0] = debug

        self.debug = debug
        self.scene.update_shaders(shader)
