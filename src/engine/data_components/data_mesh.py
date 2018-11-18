from ctypes import c_ubyte, memmove, byref


class DataMesh(object):

    def __init__(self, mesh, base_offset):
        self.mesh = mesh
        self.base_offset = base_offset
        self.indices_count = mesh.indices.size
        self.indices_offset = base_offset
        self.attribute_offset = base_offset + mesh.indices.size_bytes

    def as_bytes(self):
        offset = 0
        mesh = self.mesh
        buffer = (c_ubyte * mesh.size())()

        indices = mesh.indices
        memmove(byref(buffer), byref(indices.data), indices.size_bytes)
        offset += indices.size_bytes

        attributes = mesh.attributes
        for attr in attributes.values():
            memmove(byref(buffer, offset), byref(attr.data), attr.size_bytes)
            offset += attr.size_bytes

        return buffer

