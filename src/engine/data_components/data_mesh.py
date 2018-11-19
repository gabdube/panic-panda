from ctypes import c_ubyte, c_uint16, c_uint32, memmove, byref
from vulkan import vk


class DataMesh(object):

    def __init__(self, mesh, base_offset):
        self.mesh = mesh
        self.base_offset = base_offset

        self.indices_type = DataMesh._cache_indices_type(mesh.indices)
        self.indices_count = mesh.indices.size
        self.indices_offset = base_offset
        self.attribute_offsets = base_offset + mesh.indices.size_bytes

    def as_bytes(self):
        offset = 0
        mesh = self.mesh
        indices = mesh.indices
        attributes = mesh.attributes
        buffer = (c_ubyte * mesh.size())()

        memmove(byref(buffer), byref(indices.data), indices.size_bytes)
        offset += indices.size_bytes

        for attr in attributes.values():
            memmove(byref(buffer, offset), byref(attr.data), attr.size_bytes)
            offset += attr.size_bytes

        return buffer

    @staticmethod
    def _cache_indices_type(indices):
        base_type = indices.data._type_
        if base_type is c_uint16:
            return vk.INDEX_TYPE_UINT16
        elif base_type is c_uint32:
            return vk.INDEX_TYPE_UINT32
        else:
            raise ValueError("Index type must either be c_uint16 or c_uint32")
        
        return None