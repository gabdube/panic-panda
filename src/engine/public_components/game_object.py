class GameObject(object):

    def __init__(self):
        self.id = None
        self.shader = None
        self.mesh = None

    @classmethod
    def from_components(cls, shader, mesh):
        obj = super().__new__(cls)
        obj.__init__()
        obj.shader = shader
        obj.mesh = mesh
        return obj