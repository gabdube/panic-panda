from . import IMAGE_PATH
from collections import namedtuple
from math import log


MipmapData = namedtuple('MipmapData', ('index', 'face', 'offset', 'size', 'width', 'height'))


class EnvCubemapFile(object):
    """
        Load cubemap files exported using https://github.com/cedricpinson/envtools
        Only support the CUBE format.
    """

    def __init__(self, path, size, encoding, data):
        self.file_name = path
        self.width, self.height = size
        self.encoding = encoding
        self.mips_level = int(log(self.width, 2)) - 2  # cut the last two mipmap because the tool don't seem to export them correctly
        self.data_buffer = bytearray()
        self.mipmaps = []

        data_offset = 0
        data_length = len(data)
        data_view = memoryview(data)
        mip_extent_width, mip_extent_height = size

        for mipmap_index in range(self.mips_level):
            if data_offset >= data_length:
                break

            for face_index in range(6):
                mipmap_size_bytes = mip_extent_width * mip_extent_height * 4
                
                image_data = data_view[data_offset : data_offset+mipmap_size_bytes]
                deinterleave = bytearray(mipmap_size_bytes)
                self.deinterleaveImage4(mip_extent_width, image_data, deinterleave)
                self.data_buffer.extend(deinterleave)

                mipmap = MipmapData(mipmap_index, face_index, data_offset, mipmap_size_bytes, mip_extent_width, mip_extent_height)
                self.mipmaps.append(mipmap)
                
                data_offset += mipmap_size_bytes
            
            mip_extent_width //= 2
            mip_extent_height //= 2

        self.texture_size = len(self.data_buffer)
        
    @staticmethod
    def open(path, **params):
        keys = tuple(params.keys())
        if ("width" not in keys) or ("height" not in keys):
            raise ValueError("The image `width` and `height` must be specified as keyword arguments")
        if "format" not in keys:
            raise ValueError("The image `format` must be specified as a keyword argument ")
        if "encoding" not in keys:
            raise ValueError("The image `encoding` must be specified as a keyword argument ")

        encoding = params["encoding"].lower()

        fmt = params["format"].lower()
        if fmt != "cube":
            raise ValueError("The only supported format is CUBE")

        width, height = params["width"], params["height"]
        if width != height:
            raise ValueError("Texture must be square and a power of 2")

        with (IMAGE_PATH/path).open('rb') as f:
            data = f.read()

        return EnvCubemapFile(path, (params["width"], params["height"]), encoding, data)
        
    @staticmethod
    def deinterleaveImage4(size, src, dst):
        idx = 0
        npixel = size * size
        npixel2 = 2 * size * size
        npixel3 = 3 * size * size

        for i in range(npixel):
            dst[idx] = src[i]
            dst[idx+1] = src[i + npixel]
            dst[idx+2] = src[i + npixel2]
            dst[idx+3] = src[i + npixel3]
            idx += 4
