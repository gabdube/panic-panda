from engine import Scene, Mesh, Shader, GameObject, Image, Sampler, CombinedImageSampler
from engine.assets import GLBFile, GLTFFile, KTXFile
from system import events as evt
from utils import Mat4, Mat3
from .components import Camera, LookAtView
from math import radians, pi


class DebugNormalsScene(object):

    def __init__(self, app, engine):
        self.app = app
        self.engine = engine
        self.scene = s = Scene.empty()

        # Global state stuff
        self.shaders = ()
        self.objects = ()

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
        self.scene.update_shaders(*self.shaders)

    def update_perspective(self, event, data):
        width, height = data
        self.camera.update_perspective(60, width, height)
        self.update_objects()

    def handle_keypress(self, event, data):
        if data.key in evt.NumKeys:
            self.app.switch_scene(data) 
    
    def handle_mouse(self, event, event_data):
        if self.camera_view(event, event_data):
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

    def _setup_assets(self):
        scene = self.scene

        # Images
        helmet_f = KTXFile.open("damaged_helmet.ktx")
        helmet_f = helmet_f.slice_array(slice(2, 3))                        # Only keep the normal maps
        helmet_f = helmet_f[1:2]                                            # Only keep the first mipmap
        helmet_f.cast_single()                                              # Interpret the image as a single texture (not an array)
        helmet_maps = Image.from_ktx(helmet_f, name="HelmetTextureMaps")

        # Sampler
        helmet_sampler = Sampler.from_params(max_lod=helmet_maps.mipmaps_levels)

        # Shaders
        shader_normals_map = {"POSITION": "pos", "NORMAL": "normal", "TANGENT": "tangent", "TEXCOORD_0": "uv"}
        shader2_normals_map = {"POSITION": "pos", "NORMAL": "normal", "TEXCOORD_0": "uv"}
        
        shader_normals = Shader.from_files(
            f"debug_normals/debug_normals.vert.spv",  
            f"debug_normals/debug_normals.frag.spv",
            f"debug_normals/debug_normals.map.json",
            name="DebugNormals"
        )

        shader2_normals = Shader.from_files( 
            f"debug_normals2/debug_normals2.vert.spv",  
            f"debug_normals2/debug_normals2.frag.spv",
            f"debug_normals2/debug_normals2.map.json",
            name="DebugNormalsNoTangent"
        )

        shader_normals.uniforms.debug = { "debug1": (0, 1, 0, 0) }
        shader2_normals.uniforms.debug = { "debug1": (0, 1, 0, 0) }

        # Meshes
        helmet_m = Mesh.from_gltf(GLBFile.open("damaged_helmet.glb"), "HelmetMesh", attributes_map=shader_normals_map, name="HelmetMesh")
        helmet_m2 = Mesh.from_gltf(GLTFFile.open("DamagedHelmet.gltf"), "HelmetMesh", attributes_map=shader2_normals_map, name="HelmetMesh2")

        # Objects
        helmet = GameObject.from_components(shader = shader_normals.id, mesh = helmet_m.id, name = "Helmet")
        helmet.model = Mat4.from_rotation(radians(360), (0, 1, 0)).translate(-1, 0, 0)
        helmet.uniforms.normal_maps = CombinedImageSampler(image_id=helmet_maps.id, view_name="default", sampler_id=helmet_sampler.id)

        helmet2 = GameObject.from_components(shader = shader2_normals.id, mesh = helmet_m2.id, name = "Helmet")
        helmet2.model = Mat4().from_rotation(radians(90), (1, 0, 0)).translate(1, 0, 0)
        helmet2.uniforms.normal_maps = CombinedImageSampler(image_id=helmet_maps.id, view_name="default", sampler_id=helmet_sampler.id)

        scene.shaders.extend(shader_normals, shader2_normals)
        scene.meshes.extend(helmet_m, helmet_m2)
        scene.images.extend(helmet_maps)
        scene.samplers.extend(helmet_sampler)
        scene.objects.extend(helmet, helmet2)
        
        self.objects = (helmet, helmet2,)
        self.shaders = (shader_normals, shader2_normals)
