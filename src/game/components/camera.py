from utils.mat4 import Mat4
from math import radians


class Camera(object):

    def __init__(self, width, height):
        self.position = pos = [0,0,-1.5]

        self.projection = Mat4.perspective(radians(60), width/height, 0.001, 1000.0)
        self.view_position = Mat4.from_translation(*pos)
        self.view_rotation = Mat4.from_rotation(radians(180), (0.0, 0.0, 1.0))
        self.view_projection = self.projection * (self.view_position * self.view_rotation)

