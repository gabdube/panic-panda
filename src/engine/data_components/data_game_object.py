class DataGameObject(object):

    def __init__(self, obj):
        self.obj = obj
        self.shader = obj.shader
        self.mesh = obj.mesh
        
        self.pipeline = None
        self.descriptor_sets = None
        self.write_sets = None
        