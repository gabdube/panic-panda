from engine import Engine 
from game import MainScene
from time import sleep


class PanicPanda(object):
    
    def __init__(self):
        self.engine = Engine()
        self.main = MainScene()

    def run(self):
        engine = self.engine
        engine.load(self.main)
        engine.activate(self.main)

        while engine.running:
            engine.render()
            sleep(1/60)

    def free(self):
        self.engine.free()


def run():
    app = PanicPanda()
    app.run()
    app.free()


run()
