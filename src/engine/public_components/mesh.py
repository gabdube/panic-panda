from enum import Enum
from engine.assets import GLBFile
from . import TypedArray


class Mesh(object):

    def __init__(self):
        self.id = None
        self.indices = None
        self.attributes = None
        self.buffer = None

    @classmethod
    def from_array(cls, indices, attributes):
        mesh = super().__new__(cls)
        mesh.__init__()

        mesh.indices = indices
        mesh.attributes = attributes
        
        return mesh

    @staticmethod
    def from_gltf(gltf_file, index_or_name, attributes_map):
        if isinstance(index_or_name, str):
            mesh = next((m for m in gltf_file.layout["meshes"] if m["name"] == index_or_name), None)
            if mesh is None:
                raise ValueError(f"No mesh named {index_or_name} in gltf file")
        else:
            mesh = gltf_file.layout["meshes"][index_or_name]
                
        if isinstance(gltf_file, GLBFile):
            return Mesh.from_glb(gltf_file, mesh, attributes_map)
        else:
            raise TypeError(f"Unknown type: {type(gltf_file).__qualname__}") 

    @classmethod
    def from_glb(cls, glb, mesh, attributes_map):
        mesh0 = mesh['primitives'][0]

        indices_data = glb.accessor_data(mesh0["indices"])
        
        attributes = {}
        for attr_name, acc_index in mesh0["attributes"].items():
            mapped_name = attributes_map.get(attr_name)
            if mapped_name is not None:
                attributes[mapped_name] = glb.accessor_data(acc_index)

        mesh = super().__new__(cls)
        mesh.__init__()
        mesh.indices = TypedArray.from_memory_view(*indices_data)
        mesh.attributes = { name: TypedArray.from_memory_view(*data) for name, data in attributes.items()}
        return mesh

    def size(self):
        return self.indices.size_bytes + sum(map(lambda a: a.size_bytes, self.attributes.values()))
