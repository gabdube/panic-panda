from system import events as evt
from utils import Mat4, Vec3
from math import sin, cos, radians


class LookAtView(object):
    """
        A component that handle the camera movement for previewing a single object

        The mouse wheel zoom.
        Moving the mouse while pressing the right mouse button translate the view
        Moving the mouse while pressing the left mouse button rotate the view
    """

    def __init__(self, camera, **kwargs):
        self.mouse_state  = { btn: evt.MouseClickState.Up for btn in evt.MouseClickButton }
        self.mouse_pos = (0,0)
        
        self.mod_rotate = kwargs.get('mod_rotate', 0.005)
        self.mod_translate = kwargs.get('mod_translate', 0.005)
        self.mod_zoom = kwargs.get('mod_zoom', 0.09)

        self.bounds_zoom = kwargs.get('bounds_zoom', (-0.4, -3.0))
        self.bounds_rot_y = kwargs.get('bounds_rot_y', (radians(-89.99), radians(89.99)))

        self.position = kwargs.get('position', [0.0, 0.0, 0.0])
        self.rotation = kwargs.get('rotation', [0.0, 0.0])

        self.camera = camera
        self.look()

    def look(self):
        cam = self.camera
        px, py, pz = self.position
        rx, ry = self.rotation

        center, up = Vec3(), Vec3.from_data(0, 1, 0)

        # Rotations
        eye = Vec3.from_data(
            pz * sin(rx) * cos(ry),
            pz * sin(ry),
            pz * cos(rx) * cos(ry)
        )

        n = (eye-center).normalize()
        u = Vec3.cross_product(up, n).normalize()
        v = Vec3.cross_product(n, u).normalize()

        # Truck
        u.scale(px)
        eye += u
        center += u

        # Pedestal
        v.scale(py)
        eye += v
        center += v

        look = Mat4.look_at(eye, center, up)
        cam.update_view(look)

    def rotate_camera(self, x1, y1):
        mod = self.mod_rotate
        rot = self.rotation
        x2, y2 = self.mouse_pos
        x3, y3 = (x2-x1) * mod, (y2-y1) * mod
        min_y, max_y = self.bounds_rot_y

        rot[0] += x3
        rot[1] -= y3
        rot[1] = min(max(rot[1], min_y), max_y)

        self.mouse_pos = (x1, y1)
        self.look()

    def translate_camera(self, x1, y1):
        mod = self.mod_translate
        x2, y2 = self.mouse_pos
        x3, y3 = (x2-x1) * mod, (y2-y1) * mod

        self.position[0] += x3
        self.position[1] += y3

        self.mouse_pos = (x1, y1)
        self.look()

    def zoom_camera(self, z):
        min_z, max_z = self.bounds_zoom
        pos = self.position

        pos[2] += z * self.mod_zoom
        pos[2] = min(max(pos[2], min_z), max_z)

        self.look()

    def __call__(self, event, event_data):
        processed = False
        ms = self.mouse_state

        if event is evt.MouseClick:
            self.mouse_pos = (event_data.x, event_data.y) 
            ms[event_data.button] = event_data.state
            processed = True
            
        elif event is evt.MouseMove:
            right, left, *_ = evt.MouseClickButton
            down = evt.MouseClickState.Down

            if ms[right] is down:
                self.rotate_camera(*event_data)
                processed = True
            elif ms[left] is down:
                self.translate_camera(*event_data)
                processed = True

        elif event is evt.MouseScroll:
            self.zoom_camera(event_data.delta)
            processed = True

        return processed
