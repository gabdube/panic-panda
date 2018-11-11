# -*- coding: utf-8 -*-
"""
The windowing module export a Window interface over a system window.
"""

import platform

system_name = platform.system()
if system_name == 'Windows':
    from .win32 import Win32Window as Window
elif system_name == 'Linux':
    from .xcb import XcbWindow as Window
else:
    raise OSError(f"Os \"{system_name}\" is not supported")

del system_name
del platform
