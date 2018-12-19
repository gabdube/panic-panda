from ctypes import c_float, Structure
from itertools import chain
from math import tan, sin, cos, sqrt
from sys import float_info

buffer_type = c_float*16


class Mat4(Structure):
    
    __slots__ = ('data',)
    _fields_ = (('data', buffer_type),)

    def __init__(self):
        staging = (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        )

        self.data[::] = buffer_type(*chain(*staging))

    @classmethod
    def from_data(cls, data):
        obj = super(Mat4, cls).__new__(cls)
        obj.data[::] = buffer_type(*chain(*data))
        return obj

    @classmethod
    def look_at(cls, eye, center, up):
        e = float_info.epsilon

        eye_x, eye_y, eye_z = eye
        up_x, up_y, up_z = up
        cx, cy, cz = center

        if abs(eye_x - cx) < e and abs(eye_y - cy) < e and abs(eye_z - cz) < e:
            return Mat4()

        z0 = eye_x-cx
        z1 = eye_y-cy
        z2 = eye_z-cz

        length = 1 / sqrt(z0*z0 + z1*z1 + z2*z2)
        z0 *= length
        z1 *= length
        z2 *= length

        x0 = up_y*z2 - up_z*z1
        x1 = up_z*z0 - up_x*z2
        x2 = up_x*z1 - up_y*z0

        length = sqrt(x0 * x0 + x1 * x1 + x2 * x2)
        if length == 0:
            x0 = x1 = x2 = 0
        else:
            length = 1 / length
            x0 *= length
            x1 *= length
            x2 *= length

        y0 = z1 * x2 - z2 * x1
        y1 = z2 * x0 - z0 * x2
        y2 = z0 * x1 - z1 * x0

        length = sqrt(y0 * y0 + y1 * y1 + y2 * y2)
        if length == 0:
            y0 = y1 = y2 = 0
        else:
            length = 1 / length
            y0 *= length
            y1 *= length
            y2 *= length

        staging = (
            (x0, y0, z0, 0),
            (x1, y1, z1, 0),
            (x2, y2, z2, 0),
            (
                -(x0 * eye_x + x1 * eye_y + x2 * eye_z),
                -(y0 * eye_x + y1 * eye_y + y2 * eye_z),
                -(z0 * eye_x + z1 * eye_y + z2 * eye_z),
                1
            )
        )

        obj = super(Mat4, cls).__new__(cls)
        obj.data[::] = buffer_type(*chain(*staging))
        return obj
        
    @classmethod
    def perspective(cls, fovy, aspect, near, far):
        obj = super(Mat4, cls).__new__(cls)

        f = 1.0 / tan(fovy / 2)
        nf = 1.0 / (near - far)

        staging = (
            (f / aspect, 0.0, 0.0, 0.0),
            (0.0, f, 0.0, 0.0),
            (0.0, 0.0, (far + near) * nf, -1.0),
            (0.0, 0.0, (far * near * 2) * nf, 0.0)
        )

        obj.data[::] = buffer_type(*chain(*staging))

        return obj

    @classmethod
    def from_translation(cls, x, y, z):
        obj = super(Mat4, cls).__new__(cls)

        staging = (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (x, y, z, 1.0)
        )

        obj.data[::] = buffer_type(*chain(*staging))

        return obj

    @classmethod
    def from_rotation(cls, rad, axis):
        obj = super(Mat4, cls).__new__(cls)

        x, y, z = axis
        length = sqrt(x * x + y * y + z * z)

        if abs(length) < float_info.epsilon:
            raise ValueError()

        length = 1 / length
        x *= length
        y *= length
        z *= length

        s = sin(rad)
        c = cos(rad)
        t = 1 - c

        r1, r2, r3, r4 = ([0.0]*4 for _ in range(4))

        r1[0] = x * x * t + c
        r1[1] = y * x * t + z * s
        r1[2] = z * x * t - y * s

        r2[0] = x * y * t - z * s
        r2[1] = y * y * t + c
        r2[2] = z * y * t + x * s

        r3[0] = x * z * t + y * s
        r3[1] = y * z * t - x * s
        r3[2] = z * z * t + c

        r4[3] = 1.0

        obj.data[::] = buffer_type(*chain(r1, r2, r3, r4))

        return obj

    @classmethod
    def from_quat(cls, quat):
        obj = super(Mat4, cls).__new__(cls)
        x, y, z, w = quat.data[::]
        x2 = x + x
        y2 = y + y
        z2 = z + z

        xx = x * x2
        yx, yy = y * x2, y * y2
        zx, zy, zz = z * x2, z * y2, z * z2
        wx, wy, wz = w * x2, w * y2, w * z2

        r1 = (
            1 - yy - zz,
            yx + wz,
            zx - wy,
            0
        )

        r2 = (
            yx - wz,
            1 - xx - zz,
            zy + wx,
            0
        )

        r3 = (
            zx + wy,
            zy - wx,
            1 - xx - yy,
            0
        )

        r4 = (0,0,0,1)

        obj.data[::] = buffer_type(*chain(r1, r2, r3, r4))

        return obj

    def clone(self):
        mat = Mat4()
        mat.data[::] = self.data
        return mat

    def translate(self, x, y, z):
        data = self.data
        a00, a01, a02, a03 = data[0:4]
        a10, a11, a12, a13 = data[4:8]
        a20, a21, a22, a23 = data[8:12]
        a30, a31, a32, a33 = data[12:16]

        data[12] = a00 * x + a10 * y + a20 * z + a30
        data[13] = a01 * x + a11 * y + a21 * z + a31
        data[14] = a02 * x + a12 * y + a22 * z + a32
        data[15] = a03 * x + a13 * y + a23 * z + a33

    def get_translation(self):
        return self.data[12:15]

    def rotate(self, rad, axis):
        x, y, z = axis
        length = sqrt(x * x + y * y + z * z)

        if abs(length) < float_info.epsilon:
            raise ValueError()

        length = 1 / length
        x *= length
        y *= length
        z *= length

        s = sin(rad)
        c = cos(rad)
        t = 1 - c

        # Load the matrix into local values because it's faster than operating directly into the ctypes buffer
        data = self.data
        a00, a01, a02, a03 = data[0:4]
        a10, a11, a12, a13 = data[4:8]
        a20, a21, a22, a23 = data[8:12]

        #Construct the elements of the rotation matrix
        b00, b01, b02 = (x * x * t + c), (y * x * t + z * s), (z * x * t - y * s)
        b10, b11, b12 = ( x * y * t - z * s), (y * y * t + c), (z * y * t + x * s)
        b20, b21, b22 = (x * z * t + y * s), (y * z * t - x * s), (z * z * t + c)

        # Perform rotation-specific matrix multiplication

        staging = (
            (
                a00 * b00 + a10 * b01 + a20 * b02,
                a01 * b00 + a11 * b01 + a21 * b02,
                a02 * b00 + a12 * b01 + a22 * b02,
                a03 * b00 + a13 * b01 + a23 * b02
            ),
            (
                a00 * b10 + a10 * b11 + a20 * b12,
                a01 * b10 + a11 * b11 + a21 * b12,
                a02 * b10 + a12 * b11 + a22 * b12,
                a03 * b10 + a13 * b11 + a23 * b12
            ),
            (
                a00 * b20 + a10 * b21 + a20 * b22,
                a01 * b20 + a11 * b21 + a21 * b22,
                a02 * b20 + a12 * b21 + a22 * b22,
                a03 * b20 + a13 * b21 + a23 * b22
            ),
            data[12:16]
        )

        self.data[::] = buffer_type(*chain(*staging))
        
        return self

    def invert(self):
        data = self.data
        a00, a01, a02, a03 = data[0:4]
        a10, a11, a12, a13 = data[4:8]
        a20, a21, a22, a23 = data[8:12]
        a30, a31, a32, a33 = data[12:16]

        b00, b01, b02 = (a00 * a11 - a01 * a10), (a00 * a12 - a02 * a10), (a00 * a13 - a03 * a10)
        b03, b04, b05 = (a01 * a12 - a02 * a11), (a01 * a13 - a03 * a11), (a02 * a13 - a03 * a12)
        b06, b07, b08 = (a20 * a31 - a21 * a30), (a20 * a32 - a22 * a30), (a20 * a33 - a23 * a30)
        b09, b10, b11 = (a21 * a32 - a22 * a31), (a21 * a33 - a23 * a31), (a22 * a33 - a23 * a32)

        det = b00 * b11 - b01 * b10 + b02 * b09 + b03 * b08 - b04 * b07 + b05 * b06
        if not det:
            raise ValueError

        det = 1.0 / det

        staging = (
            (
                (a11 * b11 - a12 * b10 + a13 * b09) * det,
                (a02 * b10 - a01 * b11 - a03 * b09) * det,
                (a31 * b05 - a32 * b04 + a33 * b03) * det,
                (a22 * b04 - a21 * b05 - a23 * b03) * det
            ),
            (
                (a12 * b08 - a10 * b11 - a13 * b07) * det,
                (a00 * b11 - a02 * b08 + a03 * b07) * det,
                (a32 * b02 - a30 * b05 - a33 * b01) * det,
                (a20 * b05 - a22 * b02 + a23 * b01) * det
            ),
            (
                (a10 * b10 - a11 * b08 + a13 * b06) * det,
                (a01 * b08 - a00 * b10 - a03 * b06) * det,
                (a30 * b04 - a31 * b02 + a33 * b00) * det,
                (a21 * b02 - a20 * b04 - a23 * b00) * det
            ),
            (
                (a11 * b07 - a10 * b09 - a12 * b06) * det,
                (a00 * b09 - a01 * b07 + a02 * b06) * det,
                (a31 * b01 - a30 * b03 - a32 * b00) * det,
                (a20 * b03 - a21 * b01 + a22 * b00) * det
            )
        )

        self.data[::] = buffer_type(*chain(*staging))
        
        return self

    def transpose(self):
        d = self.data
        a01, a02, a03 = d[0:3]
        a12, a13 = d[6:8]
        a23 = d[11]

        d[1:5] = d[4], d[8], d[12], a01
        d[6:10] = d[9], d[13], a02, a12
        d[11:15] = d[14], a03, a13, a23
    
        return self

    def __mul__(self, other):
        a, b = self.data, other.data
        a00, a01, a02, a03 = a[0:4]
        a10, a11, a12, a13 = a[4:8]
        a20, a21, a22, a23 = a[8:12]
        a30, a31, a32, a33 = a[12:16]

        staging = []

        b0, b1, b2, b3 = b[0:4]
        staging.append((
            b0*a00 + b1*a10 + b2*a20 + b3*a30,
            b0*a01 + b1*a11 + b2*a21 + b3*a31,
            b0*a02 + b1*a12 + b2*a22 + b3*a32,
            b0*a03 + b1*a13 + b2*a23 + b3*a33
        ))

        b0, b1, b2, b3 = b[4:8]
        staging.append((
            b0*a00 + b1*a10 + b2*a20 + b3*a30,
            b0*a01 + b1*a11 + b2*a21 + b3*a31,
            b0*a02 + b1*a12 + b2*a22 + b3*a32,
            b0*a03 + b1*a13 + b2*a23 + b3*a33
        ))

        b0, b1, b2, b3 = b[8:12]
        staging.append((
            b0*a00 + b1*a10 + b2*a20 + b3*a30,
            b0*a01 + b1*a11 + b2*a21 + b3*a31,
            b0*a02 + b1*a12 + b2*a22 + b3*a32,
            b0*a03 + b1*a13 + b2*a23 + b3*a33
        ))

        b0, b1, b2, b3 = b[12:16]
        staging.append((
            b0*a00 + b1*a10 + b2*a20 + b3*a30,
            b0*a01 + b1*a11 + b2*a21 + b3*a31,
            b0*a02 + b1*a12 + b2*a22 + b3*a32,
            b0*a03 + b1*a13 + b2*a23 + b3*a33
        ))

        return Mat4.from_data(staging)

    def __getitem__(self, key):
        return self.data[key]

    def __len__(self):
        return 16

    def __iter__(self):
        yield from iter(self.data)
