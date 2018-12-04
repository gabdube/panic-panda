from .. import vk
from .utils import array_pointer, array, check_ctypes_members, sequence_to_array
from ctypes import c_uint, c_uint32, c_float, c_char_p, byref, c_int, pointer
from collections import namedtuple


QueueFamilyPair = namedtuple("QueueFamilyPair", ("index", "properties"))


def physical_device_memory_properties(api, physical_device_handle):
    props = vk.PhysicalDeviceMemoryProperties()
    api.GetPhysicalDeviceMemoryProperties(physical_device_handle, byref(props))
    return props


def list_physical_devices(api, instance):

    physical_devices_count = c_uint(0)
    result = api.EnumeratePhysicalDevices(instance, byref(physical_devices_count), None)
    if result != vk.SUCCESS or physical_devices_count.value == 0:
        raise RuntimeError('Could not fetch the physical devices or there are no devices available')

    buf = array(vk.PhysicalDevice, physical_devices_count.value)()
    api.EnumeratePhysicalDevices(instance, byref(physical_devices_count), array_pointer(buf))

    return tuple(vk.PhysicalDevice(b) for b in buf)


def physical_device_properties(api, physical_device_handle):
    properties = vk.PhysicalDeviceProperties()
    api.GetPhysicalDeviceProperties(physical_device_handle, byref(properties))
    return properties


def physical_device_format_properties(api, physical_device, format):
    properties = vk.FormatProperties()
    api.GetPhysicalDeviceFormatProperties(physical_device, format, byref(properties))
    return properties


def physical_device_features(api, physical_device_handle, all=False):
    """
    Return the names of the supported feature for the selected physical device.
    If `all` is set to False, return an array filled with the supported features names
    If `all` is set to True, return the features structure
    """
    features = vk.PhysicalDeviceFeatures()
    api.GetPhysicalDeviceFeatures(physical_device_handle, byref(features))

    if all:
        return features
    else:
        return [name for name, _ in features._fields_ if getattr(features, name) == 1]

def enumerate_device_extensions(api, physical_device):
    extensions_count = c_uint32(0)

    result = api.EnumerateDeviceExtensionProperties(physical_device, None, byref(extensions_count), None)
    if result != vk.SUCCESS:
        raise RuntimeError('Failed to find the device extensions. Error code: 0x{:X}'.format(result))

    extensions = array(vk.ExtensionProperties, extensions_count.value)()

    result = api.EnumerateDeviceExtensionProperties(physical_device, None, byref(extensions_count), array_pointer(extensions))
    if result != vk.SUCCESS:
        raise RuntimeError('Failed to find the instance extensions. Error code: 0x{:X}'.format(result))

    return [(ext.extension_name.decode('utf-8'), ext.spec_version) for ext in extensions]


def list_queue_families(api, physical_device):
    """List the queue families with their index for a physical device"""
    
    queue_families_count = c_uint(0)
    api.GetPhysicalDeviceQueueFamilyProperties(physical_device, byref(queue_families_count), None)

    if queue_families_count.value == 0:
        raise RuntimeError('No queues families found for the selected physical device')

    queue_families = array(vk.QueueFamilyProperties, queue_families_count.value)()
    api.GetPhysicalDeviceQueueFamilyProperties(physical_device, byref(queue_families_count), array_pointer(queue_families))

    families = []
    for index, queue_family in enumerate(queue_families):
        families.append(QueueFamilyPair(index, queue_family))

    return families


def queue_create_info(**kwargs):
    check_ctypes_members(vk.DeviceQueueCreateInfo, ('queue_family_index',), kwargs.keys())
    
    queue_count = kwargs.get('queue_count', 1)
    priorities = kwargs.get('queue_priorities', (1.0,)*queue_count)
    priorities, priorities_ptr, _ = sequence_to_array(priorities, c_float)

    return vk.DeviceQueueCreateInfo(
        type = vk.STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
        next = None, 
        flags = 0,
        queue_family_index = kwargs['queue_family_index'],
        queue_count = queue_count, 
        queue_priorities = priorities_ptr
    )


def load_functions(api, device):
    for name, function in vk.load_functions(device, vk.DeviceFunctions, api.GetDeviceProcAddr):
        setattr(api, name, function)


def create_device(api, physical_device, extensions, queue_create_infos, features=None):
    """ 
    Create a vulkan device object with the associated informations 
    
    :params:
    :api: The object holding the instance functions
    :physical_device: The physical device of the device
    :extensions: The extensions to enable for the device
    :queue_create_infos: Queue create info for the device
    :features: A PhysicalDeviceFeatures structure to use
    """
    
    device = vk.Device()
    queue_create_infos_array = array(vk.DeviceQueueCreateInfo, len(queue_create_infos), queue_create_infos)
    extensions_array = array(c_char_p, len(extensions), (e.encode('utf8') for e in extensions))

    if features is not None:
        features = pointer(features)

    device_config = vk.DeviceCreateInfo(
        type=vk.STRUCTURE_TYPE_DEVICE_CREATE_INFO, next=None, flags=0,
        queue_create_info_count=len(queue_create_infos), queue_create_infos=array_pointer(queue_create_infos_array),
        enabled_layer_count=0, enabled_layer_names=None,
        enabled_extension_count=len(extensions), enabled_extension_names=array_pointer(extensions_array),
        enabled_features = features
    )

    result = api.CreateDevice(physical_device, device_config, None, byref(device))
    if result != vk.SUCCESS:
        raise RuntimeError('Failed to create the vulkan device. Error code: 0x{:X}'.format(result))

    load_functions(api, device)

    return device

def get_queue(api, device, family_index, index):
    queue = vk.Queue(0)
    api.GetDeviceQueue(device, family_index, index, byref(queue))
    return queue


def destroy_device(api, device):
    api.DestroyDevice(device, None)


def device_wait_idle(api, device):
    result = api.DeviceWaitIdle(device)
    if result != vk.SUCCESS:
        raise RuntimeError(f"Waiting for device failed: {result}")
