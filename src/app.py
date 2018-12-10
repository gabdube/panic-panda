from engine import Engine 
from game import MainScene, DebugTexturesScene
from time import sleep


class PanicPanda(object):
    
    def __init__(self):
        self.engine = Engine()
        self.main = MainScene(self.engine)
        self.debug_texture = DebugTexturesScene(self.engine)

    def run(self):
        engine = self.engine
        #engine.load(self.main.scene)
        #engine.activate(self.main.scene)

        engine.load(self.debug_texture.scene)
        engine.activate(self.debug_texture.scene)

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
