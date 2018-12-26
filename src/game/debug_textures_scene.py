from engine import Shader, GameObject, Scene, Sampler, Image, CombinedImageSampler, Mesh, MeshPrefab
from engine.assets import GLBFile, KTXFile, EnvCubemapFile, IMAGE_PATH
from system import events as evt
from utils import Mat4
from vulkan import vk
from .components import Camera, LookAtView
from math import radians


class DebugTexturesScene(object):

    def __init__(self, app, engine):
        self.app = app
        self.engine = engine
        self.scene = s = Scene.empty()
        
        # Global state stuff
        self.visible_index = None
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

    def update_objects(self):
        objects, cam = self.objects, self.camera
        view_projection = self.camera.view_projection

        current_obj = objects[self.visible_index]
        current_obj.uniforms.view.mvp[::] = view_projection * current_obj.model

        self.scene.update_objects(current_obj)

    def update_perspective(self, event, data):
        self.camera.update_perspective(60, data.width, data.height)
        self.update_objects()

    def handle_keypress(self, event, data):
        k = evt.Keys

        if data.key in evt.NumKeys:
            self.app.switch_scene(data) 
        else:
            self.switch_objects(data)

    def switch_objects(self, data):
        k = evt.Keys
        objects, visible = self.objects, self.visible_index

        objects[visible].hidden = True

        if data.key is k.Left and visible > 0:
            visible -= 1
        elif data.key is k.Right and visible+1 < len(objects):
            visible += 1

        current_object = objects[visible]
        
        if current_object.name == "ObjArrayTexture":
            # Change array texture layer
            debug = current_object.uniforms.debug_params
            layer = debug.layer[0]
            if data.key == k.Up and layer < 3:
                debug.layer[0] += 1
            elif data.key == k.Down and layer > 0:
                debug.layer[0] -= 1
        elif current_object.name == "ObjCubeTexture":
            # Change cubemap mipmap level
            debug = current_object.uniforms.debug_params
            lod = debug.lod[0]
            if data.key == k.Up and lod < 8:
                debug.lod[0] += 0.5
            elif data.key == k.Down and lod > 0:
                debug.lod[0] -= 0.5

        objects[visible].hidden = False
        self.visible_index = visible
        self.update_objects()

    def handle_mouse(self, event, event_data):
        if self.camera_view(event, event_data):
            self.update_objects()

    def _setup_assets(self):
        scene = self.scene

        # Textures
        texture = Image.from_ktx(KTXFile.open("vulkan_logo.ktx"), name="Texture")
        array_texture = Image.from_ktx(KTXFile.open("array_test.ktx"), name="ArrayTexture")

        cubemap_args = {"width": 256, "height": 256, "encoding": "LUV", "format": "CUBE"}
        env_cubemap = EnvCubemapFile.open("unity_gareout/specular_luv.bin", **cubemap_args)
        cubemap_texture = Image.from_env_cubemap(env_cubemap, name="CubemapTexture")

        with (IMAGE_PATH/"unity_gareout/brdf_ue4.bin").open("rb") as f:
            texture_raw_data = f.read()
            texture_args = {"format": vk.FORMAT_R16G16_UNORM, "extent": (128, 128, 1), "default_view_type": vk.IMAGE_VIEW_TYPE_2D}
            raw_texture = Image.from_uncompressed(texture_raw_data, name="TextureRaw", **texture_args)

        # Samplers
        sampler = Sampler.from_params(
            address_mode_V=vk.SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
            address_mode_U=vk.SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE
        )

        sampler_lod = Sampler.from_params(
            address_mode_V=vk.SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
            address_mode_U=vk.SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE,
            max_lod=cubemap_texture.mipmaps_levels
        )


        # Shaders
        simple_name = "debug_texture/debug_texture"
        array_name = "debug_texture_array/debug_texture_array"
        cube_name = "debug_texture_cube/debug_texture_cube"
        
        shader_attributes_map = {"POSITION": "pos", "TEXCOORD_0": "uv"}

        shader_simple = Shader.from_files(f"{simple_name}.vert.spv",  f"{simple_name}.frag.spv", f"{simple_name}.map.json", name="DebugTexture")
        shader_array = Shader.from_files(f"{array_name}.vert.spv",  f"{array_name}.frag.spv", f"{array_name}.map.json", name="DebugArrayTexture")
        shader_cube = Shader.from_files(f"{cube_name}.vert.spv",  f"{cube_name}.frag.spv", f"{cube_name}.map.json", name="DebugCubeTexture")

        # Meshes
        plane_m = Mesh.from_prefab(MeshPrefab.Plane, attributes_map=shader_attributes_map, name="PlaneMesh")
        plane_m2 = Mesh.from_prefab(MeshPrefab.Plane, attributes_map=shader_attributes_map, invert_y=True, name="PlaneMesh")
        sphere_m = Mesh.from_gltf(GLBFile.open("test_sphere.glb"), "Sphere.001", attributes_map=shader_attributes_map, name="SphereMesh")

        # Objects
        plane1 = GameObject.from_components(shader = shader_simple.id, mesh = plane_m.id, name = "ObjTexture")
        plane1.model = Mat4()
        plane1.uniforms.color_texture = CombinedImageSampler(image_id=texture.id, view_name="default", sampler_id=sampler.id)

        plane2 = GameObject.from_components(shader = shader_simple.id, mesh = plane_m2.id, name = "ObjRawTexture", hidden=True)
        plane2.model = Mat4()
        plane2.uniforms.color_texture = CombinedImageSampler(image_id=raw_texture.id, view_name="default", sampler_id=sampler.id)

        plane3 = GameObject.from_components(shader = shader_array.id, mesh = plane_m.id, name = "ObjArrayTexture", hidden=True)
        plane3.model = Mat4()
        plane3.uniforms.color_texture = CombinedImageSampler(image_id=array_texture.id, view_name="default", sampler_id=sampler.id)

        sphere = GameObject.from_components(shader = shader_cube.id, mesh = sphere_m.id, name = "ObjCubeTexture", hidden=True)
        sphere.model = Mat4()
        sphere.uniforms.cube_texture = CombinedImageSampler(image_id=cubemap_texture.id, view_name="default", sampler_id=sampler_lod.id)
        
        # Add objects to scene
        scene.shaders.extend(shader_simple, shader_array, shader_cube)
        scene.samplers.extend(sampler, sampler_lod)
        scene.images.extend(texture, array_texture, raw_texture, cubemap_texture)
        scene.meshes.extend(plane_m, plane_m2, sphere_m)
        scene.objects.extend(plane1, plane2, plane3, sphere)

        self.visible_index = 0
        self.objects.extend((plane1, plane2, plane3, sphere))
