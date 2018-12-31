from . import MODEL_PATH
from ..public_components import TypedArray, TypedArrayFormat as AFmt
from ctypes import sizeof, c_ubyte
import json


class GLTFFile(object):

    def __init__(self, layout):
        self.layout = layout

    @staticmethod
    def open(path):
        layout = None
        with open(MODEL_PATH / path, 'r') as f:
            layout = json.load(f)

        return GLTFFile(layout)

    def accessor_data(self, index):
        layout = self.layout
        accessor = layout["accessors"][index]
        view = layout["bufferViews"][accessor["bufferView"]]
        buffer = layout["buffers"][view["buffer"]]

        start = accessor.get("byteOffset", 0) + view.get("byteOffset", 0)
        size_bytes = GLTFFile.accessor_size(accessor)
        acc_length = GLTFFile.accessor_length(accessor)
        acc_format = GLTFFile.accessor_format(accessor)

        with open(MODEL_PATH / buffer["uri"], 'rb') as f:
            f.seek(start, 0)
            data = f.read(size_bytes)

        return TypedArray.from_byte_array(acc_format, data)

    @staticmethod
    def accessor_size(acc):
        fmt = GLTFFile.accessor_format(acc)
        length = GLTFFile.accessor_length(acc)
        return sizeof(fmt) * GLTFFile.accessor_length(acc)

    @staticmethod
    def accessor_format(acc):
        fmt = acc["componentType"]
        if fmt == 5123:   fmt = AFmt.UInt16
        elif fmt == 5126: fmt = AFmt.Float32
        else:
            raise ValueError(f"Unkown component type {fmt}")

        return fmt

    @staticmethod
    def accessor_length(acc):
        length = acc["type"]

        if length == "SCALAR": length = 1
        elif length == "VEC2": length = 2
        elif length == "VEC3": length = 3
        elif length == "VEC4": length = 4
        else: 
            raise ValueError(f"Unkown type {length}")

        return acc["count"] * length
