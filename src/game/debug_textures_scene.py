from engine import Shader, GameObject, Scene, Sampler, Image, CombinedImageSampler, Mesh, MeshPrefab
from engine.assets import GLBFile, KTXFile
from utils.mat4 import Mat4
from system import events as evt
from vulkan import vk
from math import radians, sin, cos


class DebugTexturesScene(object):

    def __init__(self, app, engine):
        self.app = app
        self.engine = engine
        self.scene = s = Scene.empty()
        self.visible_index = None
        self.objects = [] 

        # Global state stuff
        self.mouse_state = { btn: evt.MouseClickState.Up for btn in evt.MouseClickButton }
        self.mouse_state["pos"] = (0,0)

        # Camera
        width, height = engine.window.dimensions()
        translate = -3.0
        cam_pos = [0,0, translate]
        self.camera = { 
            "translate": translate,
            "pos_vec": cam_pos,
            "pitch_roll": (0.0, 0.0),
            "pos":  Mat4.from_translation(*cam_pos),
            "rot": Mat4(),
            "proj": Mat4.perspective(radians(60), width/height, 0.001, 1000.0),
        }

        # Assets
        self._setup_assets()

        # Callbacks
        s.on_initialized = self.init_scene
        s.on_window_resized = self.update_perspective
        s.on_key_pressed = self.handle_keypress
        s.on_mouse_move = s.on_mouse_click = self.move_camera

    def init_scene(self):
        self.update_objects()

    def update_objects(self):
        objects, cam = self.objects, self.camera
        mvp = cam["proj"] * (cam["pos"] * cam["rot"])

        for obj in objects:
            obj.uniforms.view.mvp = (mvp * obj.model).data

        self.scene.update_objects(*objects)

    def update_camera(self):
        cam = self.camera
        pitch, roll = map(radians, cam["pitch_roll"])
        translate = cam["translate"]

        for obj in self.objects:
            obj.model = Mat4.from_rotation(roll,  (1.0, 0.0, 0.0))\
                            .rotate(pitch, (0.0, 1.0, 0.0))

        self.update_objects()

    def update_perspective(self, event, data):
        cam = self.camera
        
        width, height = data
        cam["proj"] = Mat4.perspective(radians(60), width/height, 0.001, 1000.0)

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
        
        if visible == 1:
            array_texture = objects[1]
            debug = array_texture.uniforms.debug_params
            layer =  debug.layer[0]
            if data.key == k.Up and layer < 5:
                debug.layer[0] += 1
            elif data.key == k.Down and layer > 0:
                debug.layer[0] -= 1
            
            self.scene.update_objects(array_texture)

        objects[visible].hidden = False
        self.visible_index = visible

    def move_camera(self, event, data):
        ms = self.mouse_state
        if event is evt.MouseClick:
            ms[data.button] = data.state
        elif event is evt.MouseMove:
            right, left, *_ = evt.MouseClickButton
            down = evt.MouseClickState.Down
            
            if ms[right] is down:
                cam = self.camera
                x1, y1 = data
                x2, y2 = ms["pos"]
                
                pitch, roll = cam["pitch_roll"]
                pitch_mod, roll_mod = (x2 - x1)*-0.5, (y2 - y1)*0.5

                cam["pitch_roll"] = (pitch + pitch_mod, roll + roll_mod)
                self.update_camera()
                
            ms["pos"] = data

    def _setup_assets(self):
        scene = self.scene

        # Textures
        texture = Image.from_ktx(KTXFile.open("brdfLUT.ktx"), name="SimpleTexture")
        array_texture = Image.from_ktx(KTXFile.open("papermill_diffuse_array.ktx"), name="ArrayTexture")
        cube_texture = Image.from_ktx(KTXFile.open("papermill_diffuse.ktx"), name="CubeTexture")

        # Samplers
        sampler = Sampler.from_params(address_mode_V=vk.SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE, address_mode_U=vk.SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE)

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
        sphere_m = Mesh.from_gltf(GLBFile.open("test_sphere.glb"), "Sphere.001", attributes_map=shader_attributes_map, name="SphereMesh")

        # Objects
        plane1 = GameObject.from_components(shader = shader_simple.id, mesh = plane_m.id, name = "ObjTexture")
        plane1.model = Mat4()
        plane1.uniforms.color_texture = CombinedImageSampler(image_id=texture.id, view_name="default", sampler_id=sampler.id)

        plane2 = GameObject.from_components(shader = shader_array.id, mesh = plane_m.id, name = "ObjArrayTexture", hidden=True)
        plane2.model = Mat4()
        plane2.uniforms.color_texture = CombinedImageSampler(image_id=array_texture.id, view_name="default", sampler_id=sampler.id)

        sphere = GameObject.from_components(shader = shader_cube.id, mesh = sphere_m.id, name = "ObjCubeTexture", hidden=True)
        sphere.model = Mat4()
        sphere.uniforms.cube_texture = CombinedImageSampler(image_id=cube_texture.id, view_name="default", sampler_id=sampler.id)

        # Add objects to scene
        scene.shaders.extend(shader_simple, shader_array, shader_cube)
        scene.samplers.extend(sampler)
        scene.images.extend(texture, array_texture, cube_texture)
        scene.meshes.extend(plane_m, sphere_m)
        scene.objects.extend(plane1, plane2, sphere)

        self.visible_index = 0
        self.objects.extend((plane1, plane2, sphere))
