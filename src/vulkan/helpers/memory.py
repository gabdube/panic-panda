from .. import vk
from .utils import check_ctypes_members
from ctypes import byref, c_void_p
from enum import IntFlag


class MemoryPropertyFlag(IntFlag):
    DeviceLocal = vk.MEMORY_PROPERTY_DEVICE_LOCAL_BIT
    HostVisible = vk.MEMORY_PROPERTY_HOST_VISIBLE_BIT
    HostCoherent = vk.MEMORY_PROPERTY_HOST_COHERENT_BIT
    Host = vk.MEMORY_PROPERTY_HOST_CACHED_BIT
    LazilyAllocated = vk.MEMORY_PROPERTY_LAZILY_ALLOCATED_BIT


def memory_allocate_info(**kwargs):
	check_ctypes_members(vk.MemoryAllocateInfo, ('allocation_size', 'memory_type_index'), kwargs.keys())
	return vk.MemoryAllocateInfo(
		type = vk.STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
		next = None,
		allocation_size = kwargs['allocation_size'],
		memory_type_index = kwargs['memory_type_index']
	)


def map_memory(api, device, memory, offset, size, flags=0):
    data = c_void_p(0)
    result = api.MapMemory(device, memory, offset, size, flags, byref(data)) 
    if result != vk.SUCCESS:
        raise RuntimeError(f'Failed to map device memory: {result}')

    return data

def unmap_memory(api, device, memory):
    api.UnmapMemory(device, memory)


def allocate_memory(api, device, info):
    memory = vk.DeviceMemory(0)
    result = api.AllocateMemory(device, byref(info), None, byref(memory))
    if result != vk.SUCCESS:
        raise RuntimeError(f'Failed to allocate device memory. Error code: {result}')

    return memory

def free_memory(api, device, memory):
    api.FreeMemory(device, memory, None)