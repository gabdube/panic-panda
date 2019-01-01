from utils import Mat4
from math import radians


class Camera(object):

    def __init__(self, fov, width, height, position=(0,0,0), rotation=(0,0,0)):
        self.position = pos = list(position)
        self.rotation = rot = list(rotation)

        rotx = Mat4.from_rotation(radians(rot[0]), (1,0,0))
        roty = Mat4.from_rotation(radians(rot[1]), (0,1,0))
        rotz = Mat4.from_rotation(radians(rot[2]), (0,0,1))
        cam = rotx * roty * rotz
        cam.translate(*pos)
        
        self.camera = cam
        self.view = view = cam.clone().invert()

        # Vulkan clip space has inverted Y and half Z.
        self.clip = Mat4.from_data((
            1.0,  0.0, 0.0, 0.0,
            0.0, -1.0, 0.0, 0.0,
            0.0,  0.0, 0.5, 0.0,
            0.0,  0.0, 0.5, 1.0
        ))

        proj = Mat4.perspective(radians(fov), width/height, 0.001, 1000.0)
        self.projection = self.clip * proj

    def update_perspective(self, fov, width, height):
        self.projection = Mat4.perspective(radians(fov), width/height, 0.001, 1000.0)
        self.projection = self.clip * self.projection
        self.view_projection = self.projection * self.view

    def update_view(self, new_view):
        self.view = new_view
        self.camera = cam = new_view.clone().invert()
        self.view_projection = self.projection * self.view
