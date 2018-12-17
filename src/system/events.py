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
MouseClickData = namedtuple("MouseClickData", "state button x y")

MouseMove = Events.MouseMove
MouseMoveData = namedtuple("MouseMoveData", "x y")

KeyPress = Events.KeyPress
KeyPressData = namedtuple("KeyPressData", "key")

keys_values = "Back Tab Clear Return Shift Control Menu Pause Capital Kana Junja Final Hanja Kanji Escape Convert " \
"Left Up Right Down " \
"_0 _1 _2 _3 _4 _5 _6 _7 _8 _9"
Keys = Enum("Keys", keys_values)

NumKeys = (Keys._0, Keys._1, Keys._2, Keys._3, Keys._4, Keys._5, Keys._6, Keys._8, Keys._9)
