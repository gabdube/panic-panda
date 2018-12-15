# -*- coding: utf-8 -*-
"""
A tool that merge multiple COMPRESSED .KTX files into a single .KTX file, using either array or cubemaps.

This tool was created to work around Compressonator ( https://github.com/GPUOpen-Tools/Compressonator ) missing features. It do not currently
supports the generation of texture array or cubemap textures from its command tool utility (although I raised an issue and that might change in the future).

Usage:

Output types:

* `--array`: Outputs a texture file representing a 2D texture array. Index of inputs file are used for array indices
* `--cube`: Output a cubemap file. The order of inputs must be "+X,-X,+Y,-Y,+Z,-Z" aka "Right, Left, Top, Bottom, Front, Back"


Auto Mode:

Auto mode (`--auto`) lets you pass a wildcard pattern instead of a list of input files. 
Ktxmerge use the files name in order to sort the inputs.  See the "Wildcard patterns" section for more info

External mipmaps:

If each mipmaps of the files are stored in separate files, passing the parameter `--mipmaps` will look for those files and 
pack them in the final output. Due to the high amount of files, this mode can only be used with `--auto`

Wildcard patterns:

example with pattern "item_*"

* array: item_1.ktx, item_2.ktx, item_3.ktx ... 
* cube: item_right.ktx, item_left.ktx, item_top.ktx ...

* array --mipmaps: item_1_0.ktx, item_1_1.ktx, item_2_0.ktx ... 
* cube --mipmaps: item_right_0.ktx, item_right_1.ktx, item_left_0.ktx ...


Examples:

`python ktxmerge.py --array --output <filename> --input <input files>`
`python ktxmerge.py --array --output foobar.ktx --input foo.ktx bar.ktx`

`python ktxmerge.py --array --auto --output <filename> --input <input wildcard>`
`python ktxmerge.py --array --auto --output foobar.ktx --input foo_*`

`python ktxmerge.py --cube --output <filename> --input <input files>`
`python ktxmerge.py --cube --output cube.ktx --input right.ktx left.ktx top.ktx bottom.ktx front.ktx back.ktx`

`python ktxmerge.py --cube --auto --output <filename> --input <input wildcard>`
`python ktxmerge.py --cube --auto --output cube.ktx --input foo_*`

`python ktxmerge.py --cube --auto --mipmaps --output <filename> --input <input wildcard>`
`python ktxmerge.py --cube --auto --mipmaps --output cube.ktx --input foo_*`

"""

from ctypes import c_uint8, c_uint32, sizeof, Structure
from collections import namedtuple
from pathlib import Path
from io import BytesIO
from enum import Enum
import sys, re


KTX_ID = (c_uint8*12)(0xAB, 0x4B, 0x54, 0x58, 0x20, 0x31, 0x31, 0xBB, 0x0D, 0x0A, 0x1A, 0x0A)
MipmapData = namedtuple('MipmapData', ('index', 'layer', 'face', 'offset', 'size', 'width', 'height'))


class KTXException(Exception):
    pass


class CubemapFaces(Enum):
    Right = 0
    Left = 1
    Top = 2
    Bottom = 3
    Front = 4
    Back = 5


class KtxHeader(Structure):
    """
    The header of a ktx file
    """
    _fields_ = (
        ('id', c_uint8*12),
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
        fields = {}
        for name, _ in self._fields_:
            value = getattr(self, name)
            fields[name] = value
                
        return f"KtxHeader({repr(fields)})"


class KTXFile(object):

    def __init__(self, fname, header, data):
        self.file_name = fname

        self.width = header.pixel_width
        self.height = max(header.pixel_height, 1)
        self.depth = max(header.pixel_depth, 1)
        self.mips_level = max(header.number_of_mipmap_levels, 1)
        self.array_element = max(header.number_of_array_elements, 1)
        self.faces = max(header.number_of_faces, 1)
        self.header = header

        if header.endianness != 0x04030201:
            raise ValueError("The endianess of this file do not match your system")

        if not self.compressed:
            raise ValueError("This tool only works with compressed file format")

        self.data = data
        self.mipmaps = []

        data_offset = 0
        mip_extent_width, mip_extent_height = self.width, self.height

        for mipmap_index in range(self.mips_level):
            mipmap_size_bytes = data[data_offset:data_offset+4].cast("I")[0]
            data_offset += 4

            for layer_index in range(self.array_element):
                for face_index in range(self.faces):
                    mipmap = MipmapData(mipmap_index, layer_index, face_index, data_offset, mipmap_size_bytes, mip_extent_width, mip_extent_height)
                    self.mipmaps.append(mipmap)

                    data_offset += mipmap_size_bytes

            mip_extent_width //= 2
            mip_extent_height //= 2

    @staticmethod
    def merge_2d(*input, **attr):
        extern_mipmap_count = attr["extern_mipmap_count"]
        extern_mipmaps = extern_mipmap_count > 0

        header = { key: None for key, _ in KtxHeader._fields_ }
        header["number_of_faces"] = attr.get('number_of_faces', 1)
        header["number_of_array_elements"] = attr.get('number_of_array_elements', 0)
        header["pixel_depth"] = 0
        header["endianness"] = 0x04030201

        if extern_mipmaps:
            header["number_of_mipmap_levels"] = extern_mipmap_count

        # Read and validate the files
        files = []
        for i in inputs:
            f = KTXFile.open(i)
            
            if f.array_element > 1:
                raise KTXException(f"File {f.file_name} is already a texture array")
            
            if f.faces > 1:
                raise KTXException(f"File {f.file_name} is a cubemap")

            if extern_mipmaps and f.mips_level > 1:
                raise KTXException(f"File {f.file_name} already has mipmaps")

            # Skip size check with extern mipmaps because I'm lazy
            if not extern_mipmaps:
                check_mismatch(header, "pixel_width", f.width)
                check_mismatch(header, "pixel_height", f.height)
                check_mismatch(header, "number_of_mipmap_levels", f.mips_level)
            elif extern_mipmaps and header["pixel_width"] is None:
                header["pixel_width"] = f.width
                header["pixel_height"] = f.height

            check_mismatch(header, "gl_type", f.header.gl_type)
            check_mismatch(header, "gl_type_size", f.header.gl_type_size)
            check_mismatch(header, "gl_format", f.header.gl_format)
            check_mismatch(header, "gl_internal_format", f.header.gl_internal_format)
            check_mismatch(header, "gl_base_internal_format", f.header.gl_base_internal_format)

            files.append(f)

        # Build the final headers
        header_filtered = {k:v for k,v in header.items() if v is not None}
        header = KtxHeader(**header_filtered)
        header.id[::] = KTX_ID

        # Write data
        data = BytesIO()
        if extern_mipmaps:
            # Mipmaps are outside the files
            mips_w = max(map(lambda i: i.width, files))
            while mips_w != 0:
                print("Mipmap level", mips_w)

                for array_layer, file in enumerate(filter(lambda f: f.width == mips_w, files)):
                    print(array_layer, file.file_name)
                    mipmap = file.find_mipmap(0)
                    #print(mipmap.size)

                    if array_layer == 0:
                        data.write(c_uint32(mipmap.size))
                        write_mipmap_size = False

                    data.write(file.mipmap_data(mipmap))
                
                mips_w //= 2
                
        else:
            # Mipmaps are inside the files
            for mipmap_level in range(header.number_of_mipmap_levels):
                print("Mipmap level", mipmap_level)
                for array_layer, file in enumerate(files):
                    print(array_layer, file.file_name)
                    mipmap = file.find_mipmap(mipmap_level)

                    if array_layer == 0:
                        data.write(c_uint32(mipmap.size))
                        
                    data.write(file.mipmap_data(mipmap))

        return KTXFile("output.ktx", header, memoryview(data.getvalue()))

    @staticmethod
    def merge_array(*inputs, extern_mipmap_count=0):
        array_len = len(inputs)

        if extern_mipmap_count > 0:
            array_len //= extern_mipmap_count

        return KTXFile.merge_2d(*inputs, number_of_array_elements=array_len, extern_mipmap_count=extern_mipmap_count)

    @staticmethod
    def merge_cube(*inputs, extern_mipmap_count=0):
        if extern_mipmap_count == 0 and len(inputs) != 6:
            raise KTXException(f"Cubemap must have exactly 6 input files, go {len(inputs)}")
        elif extern_mipmap_count > 0 and (len(inputs) // extern_mipmap_count) != 6:
            raise KTXException(f"Cubemap must have exactly 6 input files, go {len(inputs) // extern_mipmap_count}")

        return KTXFile.merge_2d(*inputs, number_of_faces=6, extern_mipmap_count=extern_mipmap_count)

    @staticmethod
    def open(path):
        """
        Load and parse a KTX texture

        :param path: The relative path of the file to load
        :return: A KTXFile texture object
        """
        header_size = sizeof(KtxHeader)
        data = length = None
        with Path(path).open('rb') as f:
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

    def find_mipmap(self, index, layer=0, face=0):
        for m in self.mipmaps:
            if m.index == index  and m.layer == layer and m.face == face:
                return m

        raise IndexError(f"No mipmap found with the following attributes: index={index}, layer={layer}, face={face}")

    def mipmap_data(self, mipmap):
        offset = mipmap.offset
        size = mipmap.size

        return self.data[offset:offset+size]

    def save(self, outfile):
        outfile.write(self.header)
        outfile.write(self.data)


def check_mismatch(obj, member, value):
    obj_value = obj.get(member, None)
    if obj_value is None:
        obj[member] = value
    elif obj_value != value:
        raise KTXException(f"Property mismatch for \"{member}\": Expected: \"{obj_value}\" / Actual: \"{value}\"")


def auto_input(pattern, cube, mipmaps):
    if mipmaps:
        array_re = re.compile("^.+?(\d+)_(\d+)\.ktx")
        cube_mipmaps_re = re.compile("^.+?(\d+)\.ktx")
    else:
        array_re = re.compile("^.+?(\d+)\.ktx")

    faces = (("_back", CubemapFaces.Back), ("_bottom", CubemapFaces.Bottom), ("_front", CubemapFaces.Front), 
             ("_left", CubemapFaces.Left), ("_right", CubemapFaces.Right), ("_top", CubemapFaces.Top))

    def array_sort(i):
        match = next(array_re.finditer(str(i)), None)
        if match is None:
            raise KTXException(f"Cannot find array index or mipmap index from filename {i}.")

        if mipmaps:
            return int(match.group(1)), int(match.group(2))
        else:
            return int(match.group(1))

    def cube_sort(i):
        file_name = str(i).lower()
        face = next((face for face_name, face in faces if face_name in file_name), None)
        if face is None:
            raise ValueError(f"Impossible to find cubemap face from filename {file_name}.")

        if mipmaps:
            match = next(cube_mipmaps_re.finditer(str(i)), None)
            if match is None:
                raise KTXException(f"Cannot find mipmap index from filename {i}.")

            return face.value, int(match.group(1))
        else:
            return face.value

    paths = list(Path('.').glob(pattern+'.ktx'))

    if cube:
        paths.sort(key=cube_sort)
    else:
        paths.sort(key=array_sort)

    return paths

def extern_mipmap_count(pattern, cube):
    mipmap_count_re = re.compile("^.+?(\d+)\.ktx")

    mip_levels = []
    for path in Path('.').glob(pattern+'.ktx'):
        match = next(mipmap_count_re.finditer(str(path)), None)
        mip_levels.append(int(match.group(1)))

    return max(mip_levels)+1


if __name__ == "__main__":
    try:
        argv = sys.argv
        array = "--array" in argv
        cube = "--cube" in argv
        auto = "--auto" in argv
        mipmaps = "--mipmaps" in argv

        if mipmaps and not auto:
            raise KTXException("Cannot use --mipmaps without --auto")

        mipmaps_count = 0
        if mipmaps:
            auto_pattern = argv[argv.index("--input")+1]
            mipmaps_count = extern_mipmap_count(auto_pattern, cube)

        if auto:
            inputs = auto_input(argv[argv.index("--input")+1], cube, mipmaps) 
        else:
            inputs = argv[argv.index("--input")+1::]

        if array:
            out_file = KTXFile.merge_array(*inputs, extern_mipmap_count=mipmaps_count)
        elif cube:
            out_file = KTXFile.merge_cube(*inputs, extern_mipmap_count=mipmaps_count)

        output = argv[argv.index("--output")+1]

        with open(output, 'wb') as out:
            out_file.save(out)

        print(f"Output saved to {output}")

    except KTXException as e:
        print(f"ERROR: {e}")
    except DeprecationWarning:
        print(__doc__)