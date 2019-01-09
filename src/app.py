from engine import Engine, QueueConf, QueueType
from system import events as evt
from game import MainScene, DebugTexturesScene, DebugNormalsScene, DebugPBRScene, DebugComputeScene
from time import sleep
import sys, traceback


class PanicPanda(object):
    
    def __init__(self):
        engine_configuration = {
            "QUEUES": (
                QueueConf.Default,
                QueueConf(name="compute", type=QueueType.Compute, required=False),
            )
        }
        
        self.engine = Engine(engine_configuration)


        self.main = MainScene(self, self.engine)
        self.debug_texture = DebugTexturesScene(self, self.engine)
        self.debug_normals = DebugNormalsScene(self, self.engine)
        #self.debug_pbr = DebugPBRScene(self, self.engine)
        self.debug_compute = DebugComputeScene(self, self.engine)

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
        elif data.key is keys._5:
            engine.load(self.debug_compute.scene)
            engine.activate(self.debug_compute.scene)

    def run(self):
        engine = self.engine
        engine.load(self.debug_compute.scene)
        engine.activate(self.debug_compute.scene)

        while engine.running:
            engine.events()
            engine.update()
            engine.render()
            sleep(1/60)

    def free(self):
        self.engine.free()


def run():
    try:

        # If we are running on a freezed executable, log everything to an external file
        if "python.exe" not in sys.executable:
            sys.stdout = open('run_log.txt', 'w')
        
        app = PanicPanda()
        app.run()
        app.free()
    except BaseException as e:
        traceback.print_exc(file=sys.stdout)

run()
