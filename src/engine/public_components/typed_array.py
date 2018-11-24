from ctypes import c_uint8, c_uint16, c_float, sizeof, byref
from enum import Enum


class TypedArrayFormat(object):
    UInt16 = c_uint16
    Float32 = c_float


class TypedArraySource(Enum):
    Array = 0
    MemoryView = 1


class TypedArray(object):

    def __init__(self):
        self.fmt = None
        self.size = None
        self.size_bytes = None
        self.data = None
        self.source = None

    def data_pointer(self):
        src = self.source
        if src is TypedArraySource.Array:
            raw_data  = self.data
        else:
            raw_data = (c_uint8 * self.size_bytes)(*self.data.tobytes())

        return byref(raw_data)

    @classmethod
    def from_array(cls, fmt, array):
        arr = super().__new__(cls)
        arr.__init__()
        arr.fmt = fmt
        arr.size = dl = len(array)
        arr.size_bytes = dl * sizeof(fmt)
        arr.data = (fmt*dl)(*array)
        arr.source = TypedArraySource.Array

        return arr

    @classmethod
    def from_memory_view(cls, fmt, size, mem):
        arr = super().__new__(cls)
        arr.fmt = fmt
        arr.size = size
        arr.size_bytes = size * sizeof(fmt)
        arr.data = mem
        arr.source = TypedArraySource.MemoryView

        return arr

