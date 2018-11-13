from ctypes import c_uint16
from ctypes import c_float


class DataArrayFormat():
    UInt16 = c_uint16
    Float32 = c_float
    

class DataArray(object):

    def __init__(self, fmt, data):
        pass
