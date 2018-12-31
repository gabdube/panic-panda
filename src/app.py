from engine import Engine 
from system import events as evt
from game import MainScene, DebugTexturesScene, DebugNormalsScene, DebugPBRScene
from time import sleep


class PanicPanda(object):
    
    def __init__(self):
        self.engine = Engine()
        self.main = MainScene(self, self.engine)
        self.debug_texture = DebugTexturesScene(self, self.engine)
        self.debug_normals = DebugNormalsScene(self, self.engine)
        #self.debug_pbr = DebugPBRScene(self, self.engine)

    def switch_scene(self, data):
        """Called from the scenes on keypress"""
        keys = evt.Keys
        engine = self.engine

        if data.key is keys._1:
            engine.load(self.main.scene)
            engine.activate(self.main.scene) 
        elif data.key is keys._2:
            engine.load(self.debug_texture.scene)
            engine.activate(self.debug_texture.scene)
        elif data.key is keys._3:
            engine.load(self.debug_normals.scene)
            engine.activate(self.debug_normals.scene)
        elif data.key is keys._4:
            return
            engine.load(self.debug_pbr.scene)
            engine.activate(self.debug_pbr.scene)

    def run(self):
        engine = self.engine
        engine.load(self.debug_normals.scene)
        engine.activate(self.debug_normals.scene)

        while engine.running:
            engine.events()
            engine.update()
            engine.render()
            sleep(1/60)

    def free(self):
        self.engine.free()


def run():
    app = PanicPanda()
    app.run()
    app.free()

run()
