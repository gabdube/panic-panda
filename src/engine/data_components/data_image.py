from ctypes import c_ubyte
from vulkan import helpers as hvk
from ..public_components import ImageSource


class DataImage(object):
    
    def __init__(self, image, base_offset):
        self.image = image
        self.base_offset = base_offset

    def as_ctypes_array(self):
        img = self.image
        if img.source_type is ImageSource.Ktx:
            src = img.source
            return hvk.array(c_ubyte, len(src.data), src.data)
        else:
            raise NotImplementedError(f"Method `as_ctypes_array` is not implemented for images of type {img.source_type}")
