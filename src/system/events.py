from enum import Enum
from collections import namedtuple


class EventsMap(dict):

    def __iter__(self):
        events = tuple(self.keys())
        for e in events:
            data = self[e]
            del self[e]
            yield e, data

    def __setitem__(self, event, event_data):
        if event in Events:
            super().__setitem__(event, event_data)
        else:
            raise KeyError(f"Invalid event type: {key}")


Events = Enum("Events", "WindowResized RenderEnable RenderDisable MouseClick MouseMove KeyPress")

WindowResized = Events.WindowResized
WindowResizedData = namedtuple('WindowResizedData', 'width height')

RenderEnable = Events.RenderEnable
RenderDisable = Events.RenderDisable

MouseClick = Events.MouseClick
MouseClickState = Enum("MouseButtonState", "Down Up")
MouseClickButton = Enum("MouseClickButton", "Left Right Middle")
MouseClickData = namedtuple("MouseClickData", "state button")

MouseMove = Events.MouseMove
MouseMoveData = namedtuple("MouseMoveData", "x y")

KeyPress = Events.KeyPress
KeyPressData = namedtuple("KeyPressData", "key")

keys_values = "Back Tab Clear Return Shift Control Menu Pause Capital Kana Junja Final Hanja Kanji Escape Convert Left Up Right Down"
Keys = Enum("Keys", keys_values)
