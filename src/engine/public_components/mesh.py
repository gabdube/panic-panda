from enum import Enum


class Mesh(object):

    def __init__(self):
        self.id = None
        self.indices = None
        self.attributes = None

    @classmethod
    def from_array(cls, indices, attributes):
        mesh = super().__new__(cls)
        mesh.__init__()
        mesh.indices = indices
        mesh.attributes = attributes
        return mesh

    def size(self):
        return self.indices.size_bytes + sum(map(lambda a: a.size_bytes, self.attributes.values()))

