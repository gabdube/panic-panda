from utils import Mat4
from math import radians


class Camera(object):

    def __init__(self, width, height, position=(0,0,1.5), rotation=(0,0,0)):
        self.position = pos = list(position)
        self.rotation = rot = list(rotation)

        self.rotation_x_bounds = (-90, 90)

        rotx = Mat4.from_rotation(radians(rot[0]), (1,0,0))
        roty = Mat4.from_rotation(radians(rot[1]), (0,1,0))
        rotz = Mat4.from_rotation(radians(rot[2]), (0,0,1))
        cam = rotx * roty * rotz
        cam.translate(*pos)
        
        self.camera = cam
        self.view = view = cam.clone().invert()
        self.projection = Mat4.perspective(radians(60), width/height, 0.001, 1000.0)

        self.view_projection = self.projection * view

    def translate(self, x, y, z):
        pos = self.position
        pos[0] += x; pos[1] += y; pos[2] += z

        self.camera.translate(x, y, z)
        self.view = self.camera.clone().invert()
        self.view_projection = self.projection * self.view

    def rotate(self, x, y, z):
        min_x, max_x = self.rotation_x_bounds
        rot = self.rotation

        rot[0] += x 
        rot[0] = max( min(rot[0], max_x), min_x)
        rot[1] += y
        rot[2] += z

        rotx = Mat4.from_rotation(radians(rot[0]), (1,0,0))
        roty = Mat4.from_rotation(radians(rot[1]), (0,1,0))
        rotz = Mat4.from_rotation(radians(rot[2]), (0,0,1))
        cam = rotx * roty * rotz
        cam.translate(*self.position)

        self.camera = cam
        self.view = view = cam.clone().invert()
        self.view_projection = self.projection * view
