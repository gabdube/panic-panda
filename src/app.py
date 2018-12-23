from engine import Engine 
from system import events as evt
from game import MainScene, DebugTexturesScene, DebugSkeletonScene, DebugPBRScene
from time import sleep


class PanicPanda(object):
    
    def __init__(self):
        self.engine = Engine()
        #self.main = MainScene(self, self.engine)
        #self.debug_texture = DebugTexturesScene(self, self.engine)
        self.debug_pbr = DebugPBRScene(self, self.engine)
        #self.debug_skeleton = DebugSkeletonScene(self, self.engine)

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
            engine.load(self.debug_pbr.scene)
            engine.activate(self.debug_pbr.scene)
        elif data.key is keys._4:
            print("Debug animations disabled while working on PBR")
            return
            engine.load(self.debug_skeleton.scene)
            engine.activate(self.debug_skeleton.scene)

    def run(self):
        engine = self.engine
        engine.load(self.debug_pbr.scene)
        engine.activate(self.debug_pbr.scene)

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
