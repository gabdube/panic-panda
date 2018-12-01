from ctypes import c_ubyte, c_uint16, c_uint32, memmove, byref
from vulkan import vk
from functools import lru_cache


class DataMesh(object):

    def __init__(self, mesh, base_offset):
        self.mesh = mesh
        self.base_offset = base_offset

        self.indices_type = None
        self.indices_count = mesh.indices.size
        self.indices_offset = base_offset

        self.attribute_offsets = None

        self._cache_indices_type()
        self._map_attribute_offsets()

    def as_ctypes_array(self):
        offset = 0
        mesh = self.mesh
        indices = mesh.indices
        attributes = mesh.attributes
        buffer = (c_ubyte * mesh.size())()

        memmove(byref(buffer), indices.data_pointer(), indices.size_bytes)
        offset += indices.size_bytes

        for attr in attributes.values():
            memmove(byref(buffer, offset), attr.data_pointer(), attr.size_bytes)
            offset += attr.size_bytes

        return buffer

    @lru_cache(maxsize=128)
    def attribute_offsets_for_shader(self, data_shader):
        offsets = self.attribute_offsets
        sorted_offsets = []

        for name in data_shader.ordered_attribute_names:
            if not name in offsets:
                raise RuntimeError(f"Mesh \"{self.mesh.name}\" is not compatible with shader \"{data_shader.shader.name}\". Missing attribute: \"{name}\"")

            sorted_offsets.append(offsets[name])

        return sorted_offsets

    def _cache_indices_type(self):
        indices_type = None
        base_type = self.mesh.indices.fmt
        if base_type is c_uint16:
            indices_type = vk.INDEX_TYPE_UINT16
        elif base_type is c_uint32:
            indices_type = vk.INDEX_TYPE_UINT32
        else:
            raise ValueError("Index type must either be c_uint16 or c_uint32")

        self.indices_type = indices_type

    def _map_attribute_offsets(self):
        offsets = {}
        offset = self.base_offset + self.mesh.indices.size_bytes

        for attr_name, attr in self.mesh.attributes.items():
            offsets[attr_name] = offset
            offset += attr.size_bytes

        self.attribute_offsets = offsets
