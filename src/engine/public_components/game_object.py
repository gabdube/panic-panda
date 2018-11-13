class GameObject(object):

    @classmethod
    def from_components(cls, shader, mesh):
        obj = super().__new__(cls)
        obj.id = None
        obj.__init__()
        return obj