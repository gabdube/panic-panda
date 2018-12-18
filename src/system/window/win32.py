# -*- coding: utf-8 -*-
"""
    Minimalistic wrapper over the Windows window api.

    Author: Gabriel Dube
"""
from ctypes import *
from ctypes.wintypes import *

from ..import events as e


### BINDINGS ###

# Extern libraries
k32 = windll.kernel32
u32 = windll.user32

# TYPES
LRESULT = c_size_t
LONG = c_int32
HCURSOR = HICON
WNDPROC = WINFUNCTYPE(LRESULT, HWND, UINT, WPARAM, LPARAM)

# Consts
CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001
CS_OWNDC = 0x0020

IDC_ARROW = LPCWSTR(32512)

WM_CREATE = 0x0001
WM_CLOSE = 0x0010
WM_QUIT = 0x0012
WM_MOUSEWHEEL = 0x020A
WM_RBUTTONDOWN = 0x0204
WM_LBUTTONDOWN = 0x0201
WM_MBUTTONDOWN = 0x0207
WM_RBUTTONUP = 0x0205
WM_LBUTTONUP = 0x0202
WM_MBUTTONUP = 0x0208
WM_MOUSEMOVE = 0x0200
WM_SIZE = 0x0005
WM_EXITSIZEMOVE = 0x0232
WM_KEYPRESS = 0x0100

MK_RBUTTON = 0x0002
MK_LBUTTON = 0x0001
MK_MBUTTON = 0x0010

VK_BACK = 0x8
VK_TAB = 0x9
VK_CLEAR = 0x0C
VK_RETURN = 0x0D
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_PAUSE = 0x13
VK_CAPITAL = 0x14
VK_KANA = 0x15
VK_JUNJA = 0x17
VK_FINAL = 0x18
VK_HANJA = 0x19
VK_KANJI = 0x19
VK_ESCAPE = 0x1B
VK_CONVERT = 0x1C
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_0 = 0x30
VK_1 = 0x31
VK_2 = 0x32
VK_3 = 0x33
VK_4 = 0x34
VK_5 = 0x35
VK_6 = 0x36
VK_7 = 0x37
VK_8 = 0x38
VK_9 = 0x39

k = e.Keys
key_map = {
    VK_BACK: k.Back,
    VK_TAB: k.Tab,
    VK_CLEAR: k.Clear, 
    VK_RETURN: k.Return,
    VK_SHIFT: k.Shift,
    VK_CONTROL: k.Control,
    VK_MENU: k.Menu,
    VK_PAUSE: k.Pause,
    VK_CAPITAL: k.Capital,
    VK_KANA: k.Kana,
    VK_JUNJA: k.Junja,
    VK_FINAL: k.Final,
    VK_HANJA: k.Hanja,
    VK_KANJI: k.Kanji,
    VK_ESCAPE: k.Escape,
    VK_CONVERT: k.Convert,
    VK_LEFT: k.Left,
    VK_UP: k.Up,
    VK_RIGHT: k.Right,
    VK_DOWN: k.Down,
    VK_0: k._0,
    VK_1: k._1,
    VK_2: k._2,
    VK_3: k._3,
    VK_4: k._4,
    VK_5: k._5,
    VK_6: k._6,
    VK_7: k._7,
    VK_8: k._8,
    VK_9: k._9,
}

WS_CLIPCHILDREN = 0x02000000
WS_CLIPSIBLINGS = 0x04000000
WS_OVERLAPPED = 0x00000000
WS_CAPTION = 0x00C00000
WS_SYSMENU = 0x00080000
WS_THICKFRAME = 0x00040000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000
WS_OVERLAPPEDWINDOW = WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX

SIZE_MAXIMIZED = 2
SIZE_RESTORED = 0

CW_USEDEFAULT = 0x80000000

SW_SHOWNORMAL = 5
SW_HIDE = 0

SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004

PM_REMOVE = 0x0001

SM_CXSCREEN = 0
SM_CYSCREEN = 1

NULL = c_void_p(0)
NULL_WSTR = LPCWSTR(0)


# Structures
class WNDCLASSEXW(Structure):
    _fields_ = (('cbSize', UINT), ('style', UINT), ('lpfnWndProc', WNDPROC), ('cbClsExtra', c_int),
                ('cbWndExtra', c_int), ('hinstance', HINSTANCE), ('hIcon', HICON), ('hCursor', HCURSOR),
                ('hbrBackground', HBRUSH), ('lpszMenuName', LPCWSTR), ('lpszClassName', LPCWSTR), ('hIconSm', HICON))

class POINT(Structure):
    _fields_ = (('x',LONG), ('y',LONG))


# Functions
def result_not_null(msg):
    def inner(value):
        if value == 0:
            raise WindowsError(msg + '\n' + FormatError())
        return value

    return inner


GetModuleHandleW = k32.GetModuleHandleW
GetModuleHandleW.restype = result_not_null('Failed to get window module')
GetModuleHandleW.argtypes = (LPCSTR,)

LoadCursorW = u32.LoadCursorW
LoadCursorW.restype = result_not_null('Failed to load cursor')
LoadCursorW.argtypes = (HINSTANCE, LPCWSTR)

RegisterClassExW = u32.RegisterClassExW
RegisterClassExW.restype = result_not_null('Failed to register class')
RegisterClassExW.argtypes = (POINTER(WNDCLASSEXW),)

DefWindowProcW = u32.DefWindowProcW
DefWindowProcW.restype = LPARAM
DefWindowProcW.argtypes = (HWND, UINT, WPARAM, LPARAM)

CreateWindowExW = u32.CreateWindowExW
CreateWindowExW.restype = result_not_null('Failed to create window')
CreateWindowExW.argtypes = (
    DWORD, LPCWSTR, LPCWSTR, DWORD, c_int, c_int, c_int, c_int, HWND, HMENU, HINSTANCE, c_void_p)

UnregisterClassW = u32.UnregisterClassW
UnregisterClassW.restype = result_not_null('Failed to unregister class')
UnregisterClassW.argtypes = (LPCWSTR, HINSTANCE)

DestroyWindow = u32.DestroyWindow
DestroyWindow.restype = HWND
DestroyWindow.argtypes = (HWND,)

ShowWindow = u32.ShowWindow
ShowWindow.restype = BOOL
ShowWindow.argtypes = (HWND, c_int)

PeekMessageW = u32.PeekMessageW
PeekMessageW.restype = BOOL
PeekMessageW.argtypes = (POINTER(MSG), HWND, UINT, UINT, UINT)

DispatchMessageW = u32.DispatchMessageW
DispatchMessageW.restype = LRESULT
DispatchMessageW.argtypes = (POINTER(MSG),)

TranslateMessage = u32.TranslateMessage
TranslateMessage.restype = BOOL
TranslateMessage.argtypes = (POINTER(MSG),)

PostQuitMessage = u32.PostQuitMessage
PostQuitMessage.restype = None
PostQuitMessage.argtypes = (c_int,)

GetClientRect = u32.GetClientRect
GetClientRect.restype = result_not_null('Failed to get window dimensions')
GetClientRect.argtypes = (HWND, POINTER(RECT))

SetWindowTextW = u32.SetWindowTextW
SetWindowTextW.restype = result_not_null('Failed to set the window name')
SetWindowTextW.argtypes = (HWND, LPCWSTR)

SetWindowPos = u32.SetWindowPos
SetWindowPos.restype = result_not_null('Failed to set the window position or size')
SetWindowPos.argtypes = (HWND, HWND, c_int, c_int, c_int, c_int, c_uint)

GetSystemMetrics = u32.GetSystemMetrics
GetSystemMetrics.restype = result_not_null('Failed to get system metrics')
GetSystemMetrics.argtypes = (c_int,)

GetCursorPos = u32.GetCursorPos
GetCursorPos.restype = result_not_null('Failed to get cursor pos')
GetCursorPos.argtypes = (POINTER(POINT),)

ScreenToClient = u32.ScreenToClient
ScreenToClient.restype = result_not_null('Failed to map cursor pos to client space')
ScreenToClient.argtypes = (HWND, POINTER(POINT))

################


class Win32Window(object):
    """
    A global window object.
    """

    def __init__(self, **kwargs):
        __allowed_kwargs = ('width', 'height')
        bad_kwargs_keys = [k for k in kwargs.keys() if k not in __allowed_kwargs]
        if len(bad_kwargs_keys) != 0 and type(self) is Win32Window:
            raise AttributeError("Some unknown keyword were found: {}".format(','.join(bad_kwargs_keys)))

        # Wrapper over the Windows window procedure. This allows the window object to be sent
        # to the wndproc in a simple and safe way.
        self.__wndproc = WNDPROC(lambda hwnd, msg, w, l: self.process_event(hwnd, msg, w, l))
        self.__class_name = f"PYTHON_WINDOW_{id(self)}"

        full_width, full_height = GetSystemMetrics(SM_CXSCREEN), GetSystemMetrics(SM_CYSCREEN),
        width, height = kwargs.get('width', 1280), kwargs.get('height', 720)
        x, y = (full_width//2) - (width//2), (full_height//2) - (height//2)

        mod = GetModuleHandleW(None)

        # Register the window class
        class_def = WNDCLASSEXW(
            cbSize=sizeof(WNDCLASSEXW),
            lpfnWndProc=self.__wndproc,
            style=CS_OWNDC,
            cbClsExtra=0, cbWndExtra=0,
            hInstance=mod, hIcon=NULL,
            hCursor=LoadCursorW(NULL, IDC_ARROW),
            hbrBackground=NULL,
            lpszMenuName=NULL_WSTR,
            lpszClassName=self.__class_name,
            hIconSm=NULL
        )

        RegisterClassExW(byref(class_def))

        # Create the window
        hwnd = CreateWindowExW(
            0, self.__class_name,
            "VulkanTests",
            WS_OVERLAPPEDWINDOW,
            x, y,
            width, height,
            NULL, NULL, mod, NULL
        )

        # Save properties
        self.__hwnd = hwnd
        self.__win32_hinstance = mod

        self.events = e.EventsMap()
        self.cached_window_size = (width, height)
        self.was_maximized = False
        self.window_resized = False
        self.must_exit = False

        Win32Window._fix_window_size(hwnd, width, height)


    def destroy(self):
        # If the application did not exit using the conventional way
        if self.__hwnd is not None:
            DestroyWindow(self.__hwnd)

        UnregisterClassW(self.__class_name, self.__win32_hinstance)
        self.__hwnd = None

    @property
    def handle(self):
        return self.__hwnd

    @property
    def module(self):
        return self.__win32_hinstance

    def set_title(self, title):
        title = c_wchar_p(title)
        SetWindowTextW(self.__hwnd, title)

    def show(self):
        """
        Make the window visible (duh)
        """
        ShowWindow(self.__hwnd, SW_SHOWNORMAL)

    def hide(self):
        ShowWindow(self.__hwnd, SW_HIDE)

    def dimensions(self, cache=True):
        """
        :return: The width and the height in a tuple
        """
        if cache:
            return self.cached_window_size

        dim = RECT()
        GetClientRect(self.__hwnd, byref(dim))
        return (dim.right, dim.bottom)

    def get_mouse_pos(self):
        p = POINT()
        GetCursorPos(byref(p))
        ScreenToClient(self.__hwnd, byref(p))
        return (p.x, p.y)

    def process_event(self, hwnd, msg, w, l):
        """
        Windows proc wrapper. Translate the system events into application events

        :param hwnd: The window handle
        :param msg: The system message identifier
        :param w: System message parameter
        :param l: System message parameter
        """

        def handle_btn(msg, down, btn):
            state = e.MouseClickState.Down if msg == down else e.MouseClickState.Up
            x, y = self.get_mouse_pos()
            self.events[e.MouseClick] = e.MouseClickData(state = state, button = btn, x = x, y = y)

        if msg == WM_MOUSEMOVE:
            x, y = float(c_short(l).value), float(c_short(l>>16).value)
            self.events[e.MouseMove] = e.MouseMoveData(x, y)

        elif msg in (WM_RBUTTONDOWN, WM_RBUTTONUP):
            handle_btn(msg, WM_RBUTTONDOWN, e.MouseClickButton.Right)

        elif msg in (WM_LBUTTONDOWN, WM_LBUTTONUP):
            handle_btn(msg, WM_LBUTTONDOWN, e.MouseClickButton.Left)

        elif msg in (WM_MBUTTONDOWN, WM_MBUTTONUP):
            handle_btn(msg, WM_MBUTTONDOWN, e.MouseClickButton.Middle)

        elif msg == WM_MOUSEWHEEL:
            x, y = self.get_mouse_pos()
            delta = c_int16(w>>16).value // 120
            self.events[e.MouseScroll] = e.MouseScrollData(delta = delta, x = x, y = y)

        elif msg == WM_KEYPRESS:
            self.events[e.KeyPress] = e.KeyPressData(
                key = key_map.get(w)
            )

        elif msg == WM_EXITSIZEMOVE:
            cwidth, cheight = self.cached_window_size
            width, height = self.dimensions(False)
            if width != cwidth or height != cheight:
                self.events[e.WindowResized] = e.WindowResizedData(width, height)
                self.cached_window_size = (width, height)

        elif msg == WM_SIZE:
            if w == SIZE_MAXIMIZED or w == SIZE_RESTORED:
                width, height = self.dimensions(False)
                self.events[e.WindowResized] = e.WindowResizedData(width, height)
                self.cached_window_size = (width, height)

        elif msg == WM_CLOSE:
            self.must_exit = True
        elif msg == WM_CREATE:
            pass
        else:
            return DefWindowProcW(hwnd, msg, w, l)

        return 0

    @staticmethod
    def translate_system_events():
        """
        Dispatch any waiting system message. The messages get evaluated in `process_event`
        """
        b = byref

        msg = MSG()
        while PeekMessageW(b(msg), NULL, 0, 0, PM_REMOVE) != 0:
            TranslateMessage(b(msg))
            DispatchMessageW(b(msg))

    # Private methods

    @staticmethod
    def _fix_window_size(handle, width, height):
        dim = RECT()
        GetClientRect(handle, byref(dim))

        delta_width = width - dim.right
        delta_height = height - dim.bottom

        SetWindowPos(handle, None, 0, 0, width + delta_width, height + delta_height, SWP_NOMOVE | SWP_NOZORDER)
