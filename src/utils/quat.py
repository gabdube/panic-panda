from ctypes import c_float, Structure
from math import pi, sin, cos


buffer_type = c_float*4


class Quat(Structure):

    __slots__ = ('data',)
    _fields_ = (('data', buffer_type),)

    def __init__(self):
        self.data[::] = (0,0,0,1)

    @classmethod
    def from_data(cls, data):
        obj = super(Quat, cls).__new__(cls)
        obj.data[::] = data
        return obj

    @classmethod
    def from_euler(cls, x, y, z):
        halfToRad = 0.5 * pi / 180.0
        x *= halfToRad
        y *= halfToRad
        z *= halfToRad

        sx, cx = sin(x), cos(x)
        sy, cy = sin(y), cos(y)
        sz, cz = sin(z), cos(z)

        obj = super(Quat, cls).__new__(cls)
        obj.data[::] = (
            sx * cy * cz - cx * sy * sz,
            cx * sy * cz + sx * cy * sz,
            cx * cy * sz - sx * sy * cz,
            cx * cy * cz + sx * sy * sz
        )

        return obj

    def __mul__(self, other):
        ax, ay, az, aw = self.data[::]
        bx, by, bz, bw = other.data[::]

        return Quat.from_data((
            ax * bw + aw * bx + ay * bz - az * by,
            ay * bw + aw * by + az * bx - ax * bz,
            az * bw + aw * bz + ax * by - ay * bx,
            aw * bw - ax * bx - ay * by - az * bz
        ))
