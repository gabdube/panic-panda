# -*- coding: utf-8 -*-
"""
Collection of high level functions used to interact with vulkan instances at a higher level
"""

from .. import vk
from .utils import array, array_pointer
from ctypes import c_char_p, pointer, byref, c_uint32, c_int


# Placeholder object that will hold the funtions pointers
class Api(object): pass


def load_functions(api, instance):
    """
    Load the instance and physical devices function pointers into obj

    :param api: The object that will hold the function pointer
    :param instance: The vulkan instance
    """

    for name, function in vk.load_functions(instance, vk.InstanceFunctions, vk.GetInstanceProcAddr):
        setattr(api, name, function)


def create_instance(extensions, layers):
    extensions = [e.encode('utf8') for e in extensions]
    layers = [l.encode('utf8') for l in layers]

    app_info = vk.ApplicationInfo(
        type=vk.STRUCTURE_TYPE_APPLICATION_INFO, next=None,
        application_name=b'TEMP', application_version=0,
        engine_name=b'TEMP', engine_version=0, api_version=vk.API_VERSION_1_0
    )

    extensions_count = len(extensions)
    layers_count = len(layers)
    _extensions = array(c_char_p, extensions_count, extensions)
    _layers = array(c_char_p, layers_count, layers)

    create_info = vk.InstanceCreateInfo(
        type=vk.STRUCTURE_TYPE_INSTANCE_CREATE_INFO, next=None, flags=0,
        application_info=pointer(app_info),

        enabled_layer_count=layers_count,
        enabled_layer_names=array_pointer(_layers),

        enabled_extension_count=extensions_count,
        enabled_extension_names=array_pointer(_extensions)
    )

    instance = vk.Instance(0)
    result = vk.CreateInstance(byref(create_info), None, byref(instance))
    if result != vk.SUCCESS:
        raise RuntimeError('Instance creation failed. Error code: 0x{:X}'.format(result))

    api = Api()
    load_functions(api, instance)

    return api, instance

def destroy_instance(api, instance):
    api.DestroyInstance(instance, None)

def enumerate_extensions():
    extensions_count = c_uint32(0)

    result = vk.EnumerateInstanceExtensionProperties(None, byref(extensions_count), None)
    if result != vk.SUCCESS:
        raise RuntimeError('Failed to find the instance extensions. Error code: 0x{:X}'.format(result))

    extensions = array(vk.ExtensionProperties, extensions_count.value)()

    result = vk.EnumerateInstanceExtensionProperties(None, byref(extensions_count), array_pointer(extensions))
    if result != vk.SUCCESS:
        raise RuntimeError('Failed to find the instance extensions. Error code: 0x{:X}'.format(result))

    return [(ext.extension_name.decode('utf-8'), ext.spec_version) for ext in extensions]


def enumerate_layers():
    layers_count = c_uint32(0)

    result = vk.EnumerateInstanceLayerProperties(byref(layers_count), None)
    if result != vk.SUCCESS:
        raise RuntimeError('Failed to find the instance layers. Error code: 0x{:X}'.format(result))

    layers = array(vk.LayerProperties, layers_count.value)()

    result = vk.EnumerateInstanceLayerProperties(byref(layers_count), array_pointer(layers))
    if result != vk.SUCCESS:
        raise RuntimeError('Failed to find the instance layers. Error code: 0x{:X}'.format(result))

    return [(layer.layer_name.decode('utf-8'), layer.spec_version) for layer in layers]
