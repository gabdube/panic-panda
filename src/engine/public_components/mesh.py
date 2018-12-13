from enum import Enum
from engine.assets import GLBFile
from . import TypedArray, TypedArrayFormat as AFmt
from ..base_types import name_generator, Id

mesh_name = name_generator("Mesh")

# Maps of default attributes exported in a GLTF file
DEFAULT_ATTRIBUTES_MAP = {
    "POSITION": "POSITION", "NORMAL": "NORMAL", "TANGENT": "TANGENT", "TEXCOORD_0": "TEXCOORD_0"
}


class MeshPrefab(Enum):
    Plane = 0


class Mesh(object):

    def __init__(self, **kwargs):
        self._id = Id()
        self.name = kwargs.get('name', next(mesh_name))
        self.indices = None
        self.attributes = None
        self.buffer = None

    @classmethod
    def from_array(cls, indices, attributes, **kwargs):
        mesh = super().__new__(cls)
        mesh.__init__(**kwargs)

        mesh.indices = indices
        mesh.attributes = attributes
        
        return mesh

    @staticmethod
    def from_gltf(gltf_file, index_or_name, **kwargs):
        if isinstance(index_or_name, str):
            mesh = next((m for m in gltf_file.layout["meshes"] if m["name"] == index_or_name), None)
            if mesh is None:
                raise ValueError(f"No mesh named {index_or_name} in gltf file")
        else:
            mesh = gltf_file.layout["meshes"][index_or_name]
                
        if isinstance(gltf_file, GLBFile):
            return Mesh.from_glb(gltf_file, mesh, **kwargs)
        else:
            raise TypeError(f"Unknown/Unsupported type: {type(gltf_file).__qualname__}") 

    @classmethod
    def from_glb(cls, glb, mesh, **kwargs):
        mesh0 = mesh['primitives'][0]
        attributes_map = kwargs.get('attributes_map', DEFAULT_ATTRIBUTES_MAP)

        indices_data = glb.accessor_data(mesh0["indices"])
        
        attributes = {}
        for attr_name, acc_index in mesh0["attributes"].items():
            mapped_name = attributes_map.get(attr_name)
            if mapped_name is not None:
                attributes[mapped_name] = glb.accessor_data(acc_index)

        mesh = super().__new__(cls)
        mesh.__init__(**kwargs)
        mesh.indices = TypedArray.from_memory_view(*indices_data)
        mesh.attributes = { name: TypedArray.from_memory_view(*data) for name, data in attributes.items()}
        return mesh

    @classmethod
    def from_prefab(cls, prefab, **params):
        attributes_map = params.get('attributes_map', DEFAULT_ATTRIBUTES_MAP)
        pname = attributes_map.get("POSITION", None)
        tex00_name = attributes_map.get("TEXCOORD_0", None)

        if prefab is MeshPrefab.Plane:
            attributes = {}
            indices = TypedArray.from_array(fmt=AFmt.UInt16, array=(0, 1, 2,  0, 3, 2))

            if pname is not None:
                attributes[pname] = TypedArray.from_array(fmt=AFmt.Float32, array=(-0.7, 0.7, 0,  0.7, 0.7, 0,  0.7, -0.7, 0,  -0.7, -0.7, 0))
            if tex00_name is not None:
                attributes[tex00_name] = TypedArray.from_array(fmt=AFmt.Float32, array=(0,1, 1,1, 1,0, 0,0))
        else:
            raise ValueError(f"Unknown built-in mesh: {builtin}")

        return Mesh.from_array(indices = indices, attributes = attributes)

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id.value = value

    def size(self):
        return self.indices.size_bytes + sum(map(lambda a: a.size_bytes, self.attributes.values()))
