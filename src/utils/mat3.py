from ctypes import c_float, Structure
from itertools import chain
from math import tan, sin, cos, sqrt
from sys import float_info

buffer_type = c_float*9


class Mat3(Structure):
    
    __slots__ = ('data',)
    _fields_ = (('data', buffer_type),)

    def __init__(self):
        staging = (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        )

        self.data[::] = buffer_type(*chain(*staging))

    @classmethod
    def from_data(cls, data):
        obj = super(Mat3, cls).__new__(cls)
        obj.data[::] = buffer_type(*chain(*data))
        return obj
    
    @classmethod
    def normal_from_mat4(cls, other):
        a = other.data
        a00, a01, a02, a03 = a[0:4]
        a10, a11, a12, a13 = a[4:8]
        a20, a21, a22, a23 = a[8:12]
        a30, a31, a32, a33 = a[12:16]

        b00 = a00 * a11 - a01 * a10
        b01 = a00 * a12 - a02 * a10
        b02 = a00 * a13 - a03 * a10
        b03 = a01 * a12 - a02 * a11
        b04 = a01 * a13 - a03 * a11
        b05 = a02 * a13 - a03 * a12
        b06 = a20 * a31 - a21 * a30
        b07 = a20 * a32 - a22 * a30
        b08 = a20 * a33 - a23 * a30
        b09 = a21 * a32 - a22 * a31
        b10 = a21 * a33 - a23 * a31
        b11 = a22 * a33 - a23 * a32

        det = b00 * b11 - b01 * b10 + b02 * b09 + b03 * b08 - b04 * b07 + b05 * b06

        if det == 0:
            raise ValueError()

        det = 1.0 / det

        staging = (
            ((a11 * b11 - a12 * b10 + a13 * b09) * det, 
             (a12 * b08 - a10 * b11 - a13 * b07) * det,
             (a10 * b10 - a11 * b08 + a13 * b06) * det),

            ((a02 * b10 - a01 * b11 - a03 * b09) * det, 
             (a00 * b11 - a02 * b08 + a03 * b07) * det,
             (a01 * b08 - a00 * b10 - a03 * b06) * det),

            ((a31 * b05 - a32 * b04 + a33 * b03) * det, 
             (a32 * b02 - a30 * b05 - a33 * b01) * det,
             (a30 * b04 - a31 * b02 + a33 * b00) * det),
        )
        
        return cls.from_data(staging)

    def __getitem__(self, key):
        return self.data[key]

    def __len__(self):
        return 9

    def __iter__(self):
        yield from iter(self.data)

