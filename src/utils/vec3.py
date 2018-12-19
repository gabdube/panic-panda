from ctypes import c_float, Structure
from math import sqrt


buffer_type = c_float*3


class Vec3(Structure):

    __slots__ = ('data',)
    _fields_ = (('data', buffer_type),)

    def __init__(self):
        self.data[::] = (0,0,0)

    @classmethod
    def from_data(cls, x, y, z):
        obj = super(Vec3, cls).__new__(cls)
        obj.data[::] = (x, y, z)
        return obj

    @classmethod
    def cross_product(cls, a, b):
        ax, ay, az = a.data[::]
        bx, by, bz = b.data[::]

        obj = super(Vec3, cls).__new__(cls)
        obj.data[::] = (
            ay * bz - az * by,
            az * bx - ax * bz,
            ax * by - ay * bx
        )

        return obj

    def scale(self, d):
        x1, y1, z1 = self.data[::]
        self.data[::] = (x1*d, y1*d, z1*d)

    def normalize(self):
        x, y, z = self.data[::]
        length = x*x + y*y + z*z
        if length > 0:
            length = 1 / sqrt(length)

        x *= length
        y *= length
        z *= length
        self.data[::] = (x, y, z)
        
        return self

    def __sub__(self, other):
        x1, y1, z1 = self.data[::]
        x2, y2, z2 = other.data[::]
        return Vec3.from_data(x1-x2, y1-y2, z1-z2)

    def __add__(self, other):
        x1, y1, z1 = self.data[::]
        x2, y2, z2 = other.data[::]
        return Vec3.from_data(x1+x2, y1+y2, z1+z2)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __len__(self):
        return 3

    def __iter__(self):
        yield from iter(self.data)

    def __repr__(self):
        return str(self.data[::])