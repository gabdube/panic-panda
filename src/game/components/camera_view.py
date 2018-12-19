from system import events as evt


class CameraView(object):
    """
        A component that handle the camera movement for previewing a single object

        The mouse wheel zoom.
        Moving the mouse while pressing the right mouse button move the camera
        Moving the mouse while pressing the left mouse button rotate the view
    """

    def __init__(self, camera):
        self.mouse_state  = { btn: evt.MouseClickState.Up for btn in evt.MouseClickButton }
        self.pos = (0,0)
        self.mod_rotate = 0.5
        self.mod_translate = 0.002
        self.mod_zoom = 0.2

        self.camera = camera

    def rotate_camera(self, x1, y1):
        mod = self.mod_rotate
        x2, y2 = self.pos
        x3, y3 = (x1-x2)*mod, (y1-y2)*mod
        self.camera.rotate(y3, -x3, 0)
        self.pos = (x1, y1)

    def translate_camera(self, x1, y1):
        mod = self.mod_translate
        x2, y2 = self.pos
        x3, y3 = (x1-x2) * mod, (y1-y2) * mod
        self.camera.translate(-x3, -y3, 0)
        self.pos = (x1, y1)

    def zoom_camera(self, z):
        z *= self.mod_zoom
        self.camera.translate(0, 0, -z)

    def __call__(self, event, event_data):
        processed = False
        ms = self.mouse_state

        if event is evt.MouseClick:
            self.pos = (event_data.x, event_data.y) 
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
