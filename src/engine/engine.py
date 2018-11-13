from system import Window

class Engine(object):

    def __init__(self):
        self.window = Window(width=800, height=600)
        self.running = False

    def load(self, scene):
        pass

    def activate(self, scene):
        self.window.show()
        self.running = True

    def render(self):
        self.running  = False

    def free(self):
        self.window.destroy()

