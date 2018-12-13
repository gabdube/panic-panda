from engine import Shader, GameObject, Scene, Sampler, Image, CombinedImageSampler, Mesh, MeshPrefab
from engine.assets import GLBFile, KTXFile
from utils.mat4 import Mat4
from system import events as evt
from math import radians


class DebugTexturesScene(object):

    def __init__(self, engine):
        self.engine = engine
        self.scene = s = Scene.empty()
        self.visible_index = None
        self.objects = []

        # Camera
        width, height = engine.window.dimensions()
        cam_pos = [0,0,-5.5]
        self.camera = { 
            "pos_vec": cam_pos,
            "pos":  Mat4.from_translation(*cam_pos),
            "proj": Mat4.perspective(radians(60), width/height, 0.001, 1000.0)
        }

        # Assets
        self._setup_assets()

        # Callbacks
        s.on_initialized = self.init_scene
        s.on_window_resized = self.update_perspective
        s.on_key_pressed = self.switch_objects

    def init_scene(self):
        self.update_objects()

    def update_objects(self):
        objects = self.objects
        cam = self.camera
        mvp = cam["proj"] * cam["pos"]

        for obj in objects:
            obj.uniforms.view.mvp = (mvp * obj.model).data

        self.scene.update_objects(*objects)

    def update_perspective(self, event, data):
        objects = self.objects
        cam = self.camera
        
        width, height = data
        cam["proj"] = Mat4.perspective(radians(60), width/height, 0.001, 1000.0)

        self.update_objects()

    def switch_objects(self, event, data):
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

    def _setup_assets(self):
        scene = self.scene

        # Textures
        texture = Image.from_ktx(KTXFile.open("brdfLUT.ktx"), name="SimpleTexture")
        array_texture = Image.from_ktx(KTXFile.open("papermill_diffuse_array.ktx"), name="ArrayTexture")
        cube_texture = Image.from_ktx(KTXFile.open("papermill_diffuse.ktx"), name="CubeTexture")

        # Samplers
        sampler = Sampler.new()

        # Shaders
        simple_name = "debug_texture/debug_texture"
        array_name = "debug_texture_array/debug_texture_array"
        cube_name = "debug_texture_cube/debug_texture_cube"
        
        shader_attributes_map = {"POSITION": "pos", "TEXCOORD_0": "uv"}
        shader_attributes_map_2 = {"POSITION": "pos", "NORMAL": "norm", "TANGENT": "tangent"}

        shader_simple = Shader.from_files(f"{simple_name}.vert.spv",  f"{simple_name}.frag.spv", f"{simple_name}.map.json", name="DebugTexture")
        shader_array = Shader.from_files(f"{array_name}.vert.spv",  f"{array_name}.frag.spv", f"{array_name}.map.json", name="DebugArrayTexture")
        shader_cube = Shader.from_files(f"{cube_name}.vert.spv",  f"{cube_name}.frag.spv", f"{cube_name}.map.json", name="DebugCubeTexture")
        shader_cube.uniforms.cube_texture = CombinedImageSampler(image_id=cube_texture.id, view_name="default", sampler_id=sampler.id)
        
        # Meshes
        plane_m = Mesh.from_prefab(MeshPrefab.Plane, attributes_map=shader_attributes_map, name="PlaneMesh")
        sphere_m = Mesh.from_gltf(GLBFile.open("test_sphere.glb"), "Sphere.001", attributes_map=shader_attributes_map_2, name="SphereMesh")
      
        # Objects
        plane1 = GameObject.from_components(shader = shader_simple.id, mesh = plane_m.id, name = "ObjTexture")
        plane1.model = Mat4.from_translation(0.0, 0.0, 3.0)
        plane1.uniforms.color_texture = CombinedImageSampler(image_id=texture.id, view_name="default", sampler_id=sampler.id)

        plane2 = GameObject.from_components(shader = shader_array.id, mesh = plane_m.id, name = "ObjArrayTexture", hidden=True)
        plane2.model = Mat4.from_translation(0.0, 0.0, 3.0)
        plane2.uniforms.color_texture = CombinedImageSampler(image_id=array_texture.id, view_name="default", sampler_id=sampler.id)

        sphere = GameObject.from_components(shader = shader_cube.id, mesh = sphere_m.id, name = "ObjCubeTexture", hidden=True)
        sphere.model = Mat4.from_translation(0.0, 0.0, 3.0)
        sphere.uniforms.view = {"normal": Mat4().data, "model": Mat4().data}

        # Add objects to scene
        scene.shaders.extend(shader_simple, shader_array, shader_cube)
        scene.samplers.extend(sampler)
        scene.images.extend(texture, array_texture, cube_texture)
        scene.meshes.extend(plane_m, sphere_m)
        scene.objects.extend(plane1, plane2, sphere)

        self.visible_index = 0
        self.objects.extend((plane1, plane2, sphere))
