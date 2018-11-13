class Mesh(object):
    
    @classmethod
    def from_array(cls, indices, attributes):
        mesh = super().__new__(cls)
        mesh.id = None
        mesh.__init__()
        return mesh
