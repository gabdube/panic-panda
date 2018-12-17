from system import events as evt


class CameraView(object):

    def __init__(self, camera):
        self.mouse_state  = { btn: evt.MouseClickState.Up for btn in evt.MouseClickButton }
        self.pos = (0,0)

        self.camera = camera

    def translate_camera(self, x1, y1):
        x2, y2 = self.pos
        #self.camera.move(x1-x2, y1-y2)
        self.pos = (x1, y1)

    def __call__(self, event, event_data):
        ms = self.mouse_state
        if event is evt.MouseClick:
            self.pos = (event_data.x, event_data.y)
            print(self.pos)
            ms[event_data.button] = event_data.state
            
        elif event is evt.MouseMove:
            cam = self.camera
            right, left, *_ = evt.MouseClickButton
            down = evt.MouseClickState.Down

            if ms[right] is down:
                pass
            elif ms[left] is down:
                self.translate_camera(*event_data)
