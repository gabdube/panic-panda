
class Shader(object):

    @classmethod
    def from_files(cls, vert, frag, mapping):
        shader = super().__new__(cls)
        shader.id = None
        shader.__init__()
        return shader
