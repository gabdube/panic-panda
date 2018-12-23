# -*- coding: utf-8 -*-

from . import bytes_to_cstruct, IMAGE_PATH
from vulkan import vk, helpers as hvk
from ctypes import Structure, c_ubyte, c_uint32, sizeof, memmove
from collections import namedtuple
from pathlib import Path
from io import BytesIO
import struct

KTX_ID = hvk.array(c_ubyte, 12, (0xAB, 0x4B, 0x54, 0x58, 0x20, 0x31, 0x31, 0xBB, 0x0D, 0x0A, 0x1A, 0x0A))

# OPENGL to VULKAN texture format conversion table (not included: textureCompressionETC2 / textureCompressionASTC_LDR )
GL_TO_VK_FORMATS = {

    #
    # VULKAN FEATURES: textureCompressionBC
    #

    # S3TC Compressed Texture Image Formats
    0x83F0: (vk.FORMAT_BC1_RGB_UNORM_BLOCK, vk.FORMAT_BC1_RGB_SRGB_BLOCK),
    0x83F1: (vk.FORMAT_BC1_RGBA_UNORM_BLOCK, vk.FORMAT_BC1_RGBA_SRGB_BLOCK),
    0x83F2: (vk.FORMAT_BC2_UNORM_BLOCK, vk.FORMAT_BC2_SRGB_BLOCK),
    0x83F3: (vk.FORMAT_BC3_UNORM_BLOCK, vk.FORMAT_BC3_SRGB_BLOCK),

    # RGTC Compressed Texture Image Formats
    0x8DBB: vk.FORMAT_BC4_UNORM_BLOCK,
    0x8DBC: vk.FORMAT_BC4_SNORM_BLOCK,
    0x8DBD: vk.FORMAT_BC5_UNORM_BLOCK,
    0x8DBE: vk.FORMAT_BC5_SNORM_BLOCK,

    # BPTC Compressed Texture Image Formats
    0x8E8F: vk.FORMAT_BC6H_UFLOAT_BLOCK,
    0x8E8E: vk.FORMAT_BC6H_SFLOAT_BLOCK,
    0x8E8C: vk.FORMAT_BC7_UNORM_BLOCK,
    0x8E8D: vk.FORMAT_BC7_SRGB_BLOCK,
}


MipmapData = namedtuple('MipmapData', ('index', 'layer', 'face', 'offset', 'size', 'width', 'height'))


class KtxHeader(Structure):
    """
    The header of a ktx file
    """
    _fields_ = (
        ('id', c_ubyte*12),
        ('endianness', c_uint32),
        ('gl_type', c_uint32),
        ('gl_type_size', c_uint32),
        ('gl_format', c_uint32),
        ('gl_internal_format', c_uint32),
        ('gl_base_internal_format', c_uint32),
        ('pixel_width', c_uint32),
        ('pixel_height', c_uint32),
        ('pixel_depth', c_uint32),
        ('number_of_array_elements', c_uint32),
        ('number_of_faces', c_uint32),
        ('number_of_mipmap_levels', c_uint32),
        ('bytes_of_key_value_data', c_uint32),
    )

    def __repr__(self):
        return repr({n: v for n, v in [(n[0], getattr(self, n[0])) for n in self._fields_]})


class KTXFile(object):
    """
    A class that opens KTX files. Support simple texture, array texture and cubemaps.
    Only support compressed format, for the actual list see `GL_TO_VK_FORMATS`.

    Usage:
        `KTXFile.open(file_path, **options)`

    Options:
        mipmaps_range / (int, int)
           A tuple of (start, end) to load a subset of the texture mipmaps. 
           If `end` is `None`, the mipmaps will be read until the end is reached.

    """

    def __init__(self, fname, header, data):
        self.file_name = fname
        self.header = header

        if header.endianness != 0x04030201:
            raise ValueError("The endianess of this file do not match your system")
        elif not self.compressed:
            raise ValueError("This tool only works with compressed file format")

        self.width = header.pixel_width
        self.height = max(header.pixel_height, 1)
        self.depth = max(header.pixel_depth, 1)
        self.mips_level = max(header.number_of_mipmap_levels, 1)
        self.array_element = max(header.number_of_array_elements, 1)
        self.faces = max(header.number_of_faces, 1)
        
        self.data = data
        self.mipmaps = []

        # Load mipmaps
        data_offset = 0
        mip_extent_width, mip_extent_height = self.width, self.height

        for mipmap_index in range(0, self.mips_level):
            mipmap_size_bytes = data[data_offset:data_offset+4].cast("I")[0]
            data_offset += 4

            for layer_index in range(self.array_element):
                for face_index in range(self.faces):
                    mipmap = MipmapData(mipmap_index, layer_index, face_index, data_offset, mipmap_size_bytes, mip_extent_width, mip_extent_height)
                    self.mipmaps.append(mipmap)
                    
                    data_offset += mipmap_size_bytes

            mip_extent_width //= 2
            mip_extent_height //= 2

        # Compute the texture true size (without the mipmap size indicator)
        self.texture_size = sum(m.size for m in self.mipmaps)

    @staticmethod
    def open(path):
        """
        Load and parse a KTX texture

        :param path: The relative path of the file to load
        :return: A KTXFile texture object
        """
        header_size = sizeof(KtxHeader)
        data = length = None
        with Path(IMAGE_PATH / path).open('rb') as f:
            data = memoryview(f.read())
            length = len(data)

        # File size check
        if length < header_size:
            msg = "The file ID is invalid: length inferior to the ktx header"
            raise IOError(msg.format(path))

        # Header check
        header = KtxHeader.from_buffer_copy(data[0:header_size])
        if header.id[::] != KTX_ID[::]:
            msg = "The file ID is invalid: header do not match the ktx header"
            raise IOError(msg.format(path))

        offset = sizeof(KtxHeader) + header.bytes_of_key_value_data
        texture = KTXFile(path, header, data[offset::])

        return texture

    @property
    def compressed(self):
        return self.header.gl_format == 0

    @property
    def cubemap(self):
        return self.faces == 6
    
    @property
    def array(self):
        return self.header.number_of_array_elements >= 1

    @property
    def vk_format(self):
        """
            Check the format of the texture
            :return: The vulkan format identifier
        """
        h = self.header
        is_compressed = h.gl_type == 0 and h.gl_type_size == 1 and h.gl_format == 0
        if not is_compressed:
            raise ValueError("Uncompressed file formats not currently supported")

        formats = GL_TO_VK_FORMATS.get(h.gl_internal_format, (None, None))
        fmt = formats if isinstance(formats, int) else formats[0]   # Dirty workaround until SRGB is implemented

        if fmt is None:
            raise ValueError("The format of this texture is not current supported")

        return fmt

    @property
    def vk_target(self):
        """
            Get the target of a ktx texture based on the header data
        """

        if self.height == 0:
            return vk.IMAGE_TYPE_1D
        elif self.depth > 0:
            return vk.IMAGE_TYPE_3D

        return vk.IMAGE_TYPE_2D

    @property
    def vk_view_type(self):
        """
            Get the default view type of a ktx texture based on the header data
        """
        view_type = vk.IMAGE_VIEW_TYPE_2D
        if self.cubemap:
            view_type = vk.IMAGE_VIEW_TYPE_CUBE
        elif self.array:
            view_type = vk.IMAGE_VIEW_TYPE_2D_ARRAY

        return view_type

    @property
    def vk_flags(self):
        flags = 0
        if self.cubemap:
            flags |= vk.IMAGE_CREATE_CUBE_COMPATIBLE_BIT

        return flags

    def find_mipmap(self, index, layer=0, face=0):
        for m in self.mipmaps:
            if m.index == index  and m.layer == layer and m.face == face:
                return m

        raise IndexError(f"No mipmap found with the following attributes: index={index}, layer={layer}, face={face}")

    def mipmap_data(self, mipmap):
        offset = mipmap.offset
        size = mipmap.size
        return self.data[offset:offset+size]

    def slice_mipmaps(self, mips_slice):
        header = self.header
        
        header_copy = KtxHeader()
        for key, _ in KtxHeader._fields_:
            v = getattr(header, key)
            setattr(header_copy, key, v)

        start, stop = mips_slice.start, mips_slice.stop
        mips_length = stop-start

        width, height = self.width, self.height
        for _ in range(start):
            width //= 2
            height //= 2

        header.pixel_width = width
        header.pixel_height = height
        header.number_of_mipmap_levels = mips_length

        data = BytesIO()
        for mipmap_level in range(start, stop):
            for layer_index in range(self.array_element):
                for face_index in range(self.faces):
                    mipmap = self.find_mipmap(mipmap_level, layer_index, face_index)
                    if layer_index == 0 and face_index == 0:
                        print(mipmap_level)
                        data.write(c_uint32(mipmap.size))
                    data.write(self.mipmap_data(mipmap))

        return KTXFile(self.file_name, header, memoryview(data.getvalue()))
        

    def save(self, outfile):
        outfile.write(self.header)
        outfile.write(self.data)

    def __len__(self):
        return self.mipmaps_levels

    def __getitem__(self, key):
        if isinstance(key, int):
            mips_slice = slice(key, key+1)
        elif isinstance(key, slice):
            start = key.start
            stop = key.stop
            if key.start is None:
                start = 0
            if key.stop is None:
                stop = self.mips_level
            if key.step is not None and key.step > 1:
                raise ValueError("KTXImage mipmap step must be 1")
            
            mips_slice = slice(start, stop)
        else:
            raise ValueError("KTXImage mipmap index must be int or slice")

        return self.slice_mipmaps(mips_slice)        
