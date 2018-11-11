# -*- coding: utf-8 -*-
"""
Low level utilities not related to vulkan
"""
from .. import vk
from ctypes import c_ubyte, c_float, sizeof, cast, memmove, POINTER


def array(type_, count, data=None):
    """
    Generates a ctypes array of `type` with a length of `count`

    :param type_: A ctype type (ex: c_uint)
    :param count: The array length
    :param data: The initial data (optional)
    :return: The new type (if data is None) or a new array (if data is not None)
    """
    array_type = type_*count
    if data is None:
        return array_type
    else:
        return array_type(*data)


def array_pointer(value, t=None):
    """
    Cast a ctypes array to a pointer to the array base type.

    x = (c_int*5)(1,2,4,5) # x is an array of 5 c_int
    x = array_pointer(x)   # x is a pointer to an unspecified amount of c_int

    :param value: The value to cast
    :param t: Pointed value type, if ignored use the array base type
    :return: A pointer value
    """
    return cast(value, POINTER(t or value._type_))


def sequence_to_array(seq, type):
    """
        Cast a python sequence into a ctypes array. Return the array,
        a pointer cast to the array and the count of the array.
    """
    seq_ptr, count = None, 0
    if seq is not None and len(seq) > 0:
        count = len(seq)
        seq = array(type, count, seq)
        seq_ptr = array_pointer(seq)
    
    return seq, seq_ptr, count
        

def check_ctypes_members(ctype, required, args):
    fields = tuple(map(lambda f: f[0], ctype._fields_))
    for a in args:
        if not a in fields:
            raise KeyError(f"Invalid key argument. \"{a}\" is not a member of {ctype.__qualname__}.")

    for r in required:
        if not r in args:
            raise KeyError(f"Required argument \"{r}\" was not set.")


def format_size(format):
    """ Return the size in bytes of a format unit """
    if format == vk.FORMAT_R32G32B32_SFLOAT:
        return sizeof(c_float) * 3
    elif format == vk.FORMAT_R32G32B32A32_SFLOAT:
        return sizeof(c_float) * 4
    elif format == vk.FORMAT_R32G32_SFLOAT:
        return sizeof(c_float) * 2
    else:
        raise ValueError("Format not supported")


def copy_bytes(dst_ptr, dst_offset, src_data):
    memmove(dst_ptr.value + dst_offset, src_data, len(src_data))


def bytes_to_cstruct(bytes_array, struct_view):
    """
    Cast an array of python bytes into a ctypes Structure.
    The bytes_array length must match the size of struct_view.

    :param bytes_array: The array of bytes to cast
    :param struct_view: The ctypes Structure type
    :return: An instanced Structure type
    """
    array_len = sizeof(struct_view)
    c_array = (c_ubyte * array_len)(*bytes_array[0:array_len])
    c_struct = cast(c_array, POINTER(struct_view))
    return c_struct[0]
