from engine import Scene, Mesh, Shader, GameObject, Image, Sampler, CombinedImageSampler
from engine.assets import GLBFile, KTXFile
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
        self.shader = None
        self.objects = []
        self.mouse_state = { btn: evt.MouseClickState.Up for btn in evt.MouseClickButton }
        self.mouse_state["pos"] = (0,0)

        # Camera
        width, height = engine.window.dimensions()
        self.projection = Mat4.perspective(radians(45), width/height, 0.01, 100.0)
        self.roll = pi
        self.pitch = 0.0
        self.translate = 2.8
        self.mouse_state = { btn: evt.MouseClickState.Up for btn in evt.MouseClickButton }
        self.mouse_pos = None

        # Assets
        self._setup_assets()

        # Callbacks
        s.on_initialized = self.init_scene
        s.on_window_resized = self.update_perspective
        s.on_key_pressed = self.handle_keypress
        s.on_mouse_move = s.on_mouse_click = s.on_mouse_scroll = self.handle_mouse

    def init_scene(self):
        self.update_objects()
        self.scene.update_shaders(self.shader)

    def update_perspective(self, event, data):
        width, height = data
        self.projection = Mat4.perspective(radians(60), width/height, 0.001, 1000.0)
    
        self.update_objects()

    def handle_keypress(self, event, data):
        if data.key in evt.NumKeys:
            self.app.switch_scene(data) 
    
    def handle_mouse(self, event, event_data):
        processed = False

        if event is evt.MouseClick:
            self.mouse_pos = (event_data.x, event_data.y) 
            self.mouse_state[event_data.button] = event_data.state
            processed = True
            
        elif event is evt.MouseMove:
            right, left, *_ = evt.MouseClickButton
            down = evt.MouseClickState.Down

            if self.mouse_state[right] is down:
                last_x, last_y = self.mouse_pos
                new_x, new_y = (event_data.x, event_data.y)

                delta_x = new_x - last_x
                self.roll += (delta_x / 100.0)

                delta_y = new_y - last_y
                self.pitch += (delta_y / 100.0)

                self.mouse_pos = new_x, new_y

                processed = True

        if processed:
            self.update_objects()

    def update_objects(self):
        objects = self.objects
        
        clip = Mat4.from_data((
            1.0,  0.0, 0.0, 0.0,
            0.0, -1.0, 0.0, 0.0,
            0.0,  0.0, 0.5, 0.0,
            0.0,  0.0, 0.5, 1.0
        ))

        projection = clip * self.projection

        view_x = Mat4.from_rotation(self.roll, (0,1,0))
        view_y = Mat4.from_rotation(self.pitch, (1,0,0))
        view = view_y * view_x
        view.data[14] = -self.translate

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
        shader_normals = Shader.from_files(
            f"debug_normals/debug_normals.vert.spv",  
            f"debug_normals/debug_normals.frag.spv",
            f"debug_normals/debug_normals.map.json",
            name="DebugNormals"
        )

        shader_normals.uniforms.debug = {
            "debug1": (0, 1, 0, 0)
        }

        # Meshes
        sphere_m = Mesh.from_gltf(GLBFile.open("test_sphere.glb"), "Sphere.001", attributes_map=shader_normals_map, name="SphereMesh")
        helmet_m = Mesh.from_gltf(GLBFile.open("damaged_helmet.glb"), "HelmetMesh", attributes_map=shader_normals_map, name="HelmetMesh")

        # Objects
        helmet = GameObject.from_components(shader = shader_normals.id, mesh = helmet_m.id, name = "Helmet")
        helmet.model = Mat4.from_rotation(radians(180), (1, 0, 0))
        helmet.uniforms.normal_maps = CombinedImageSampler(image_id=helmet_maps.id, view_name="default", sampler_id=helmet_sampler.id)

        scene.shaders.extend(shader_normals)
        scene.meshes.extend(sphere_m, helmet_m)
        scene.images.extend(helmet_maps)
        scene.samplers.extend(helmet_sampler)
        scene.objects.extend(helmet)
        self.objects.extend((helmet,))
        self.shader = shader_normals
