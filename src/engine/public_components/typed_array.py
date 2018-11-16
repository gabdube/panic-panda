from ctypes import c_uint16, c_float, sizeof


class TypedArrayFormat(object):
    UInt16 = c_uint16
    Float32 = c_float
    

class TypedArray(object):

    def __init__(self, fmt, data):
        self.fmt = fmt
        self.data_length = dl = len(data)
        self.data = (fmt*dl)(*data)

    def size(self):
        return len(self.data) * sizeof(self.fmt)
