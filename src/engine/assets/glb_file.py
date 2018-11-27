from . import bytes_to_cstruct, MODEL_PATH
from ..public_components import TypedArrayFormat as AFmt
from ctypes import Structure, c_uint32, sizeof
import json


class FileHeader(Structure):
    _fields_ = (("magic", c_uint32), ("version", c_uint32), ("length", c_uint32))

class ChunkHeader(Structure):
    _fields_ = (("length", c_uint32), ("type", c_uint32))


class GLBFile(object):

    def __init__(self, layout, buffer):
        self.layout = layout
        self.buffer = memoryview(buffer)

    @staticmethod
    def open(path):
        with (MODEL_PATH / path).open('rb') as f:
            raw_data = f.read()

            file_header = bytes_to_cstruct(raw_data[0:12], FileHeader)
            json_chunk_header = bytes_to_cstruct(raw_data[12:20], ChunkHeader)

            json_start = 20
            json_end = json_start + json_chunk_header.length
            json_data = json.loads(raw_data[json_start:json_end].decode("utf-8"))

            bin_head_start = json_end
            bin_head_end = bin_head_start + 8
            bin_chunk_header = bytes_to_cstruct(raw_data[bin_head_start:bin_head_end], ChunkHeader)

            bin_start = bin_head_end
            bin_end = bin_start + bin_chunk_header.length
            bin_data = bytes(raw_data[bin_start:bin_end])

        return GLBFile(json_data, bin_data)

    def accessor_data(self, index):
        layout = self.layout
        accessor = layout["accessors"][index]
        view = layout["bufferViews"][accessor["bufferView"]]

        start = accessor.get("byteOffset", 0) + view.get("byteOffset", 0)
        end = start + GLBFile.accessor_size(accessor)
        acc_length = GLBFile.accessor_length(accessor)
        acc_format = GLBFile.accessor_format(accessor)

        return acc_format, acc_length, self.buffer[start:end] 

    @staticmethod
    def accessor_size(acc):
        fmt = GLBFile.accessor_format(acc)
        length = GLBFile.accessor_length(acc)
        return sizeof(fmt) * GLBFile.accessor_length(acc)

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
        elif length == "VEC3": length = 3
        elif length == "VEC4": length = 4
        else: 
            raise ValueError(f"Unkown type {length}")

        return acc["count"] * length
