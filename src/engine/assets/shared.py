from ctypes import sizeof, c_ubyte, cast, POINTER


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
