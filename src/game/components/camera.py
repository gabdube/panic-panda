from utils import Mat4
from math import radians


class Camera(object):

    def __init__(self, width, height, position=(0,0,0), rotation=(0,0,0)):
        self.position = pos = list(position)
        self.rotation = rot = list(rotation)

        rotx = Mat4.from_rotation(radians(rot[0]), (1,0,0))
        roty = Mat4.from_rotation(radians(rot[1]), (0,1,0))
        rotz = Mat4.from_rotation(radians(rot[2]), (0,0,1))
        cam = rotx * roty * rotz
        cam.translate(*pos)
        
        self.camera = cam
        self.view = view = cam.clone().invert()
        self.projection = Mat4.perspective(radians(60), width/height, 0.001, 1000.0)

        self.view_projection = self.projection * view

    def update_view(self, new_view):
        self.view = new_view
        self.camera = cam = new_view.clone().invert()

        tr = cam.get_translation()
        self.position = [-tr[0], -tr[1], tr[2]]   # I have no idea why I must invert the x and y components

        self.view_projection = self.projection * self.view

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
