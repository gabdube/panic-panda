from engine import Scene


class DebugTexturesScene(object):

    def __init__(self, engine):
        self.engine = engine
        self.scene = s = Scene.empty()
        self.shaders = {}
        self.objects = {}


