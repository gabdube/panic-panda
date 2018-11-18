from ctypes import c_uint16, c_float, sizeof


class TypedArrayFormat(object):
    UInt16 = c_uint16
    Float32 = c_float
    

class TypedArray(object):

    def __init__(self, fmt, data):
        self.fmt = fmt
        self.size = dl = len(data)
        self.size_bytes = dl * sizeof(fmt)
        self.data = (fmt*dl)(*data)