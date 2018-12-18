from ctypes import c_float, Structure


buffer_type = c_float*4


class Quat(Structure):

    __slots__ = ('data',)
    _fields_ = (('data', buffer_type),)

    def __init__(self):
        self.data[::] = (0,0,0,1)
