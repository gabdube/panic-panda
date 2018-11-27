from vulkan import vk, helpers as hvk
from enum import IntFlag
from functools import lru_cache
from ctypes import memmove, byref, c_void_p, POINTER
import weakref


class MemoryManager(object):

    def __init__(self, engine):
        self.engine = engine
        self.memory_info = {}
        self.allocations = []
        self._setup_memory_info()

    def free(self):
        _, api, device = self.ctx

        for alloc in self.allocations:
            hvk.free_memory(api, device, alloc.device_memory)

        del self.engine
    
    @property
    def ctx(self):
        ctx = self.engine
        api, device = ctx.api, ctx.device
        return ctx, api, device

    def alloc(self, resource, resource_type, types):
        _, api, device = self.ctx

        requirements = self.get_resource_requirements(resource, resource_type)
        memory_type_index = self._get_memory_type_index(types)

        device_memory = hvk.allocate_memory(api, device, hvk.memory_allocate_info(
            allocation_size = requirements.size,
            memory_type_index = memory_type_index
        ))

        if resource_type == vk.STRUCTURE_TYPE_IMAGE_CREATE_INFO:
            hvk.bind_image_memory(api, device, resource, device_memory)
        elif resource_type == vk.STRUCTURE_TYPE_BUFFER_CREATE_INFO:
            hvk.bind_buffer_memory(api, device, resource, device_memory, 0)
        else:
            raise ValueError("value of argument \"resource_type\" must be STRUCTURE_TYPE_IMAGE_CREATE_INFO or STRUCTURE_TYPE_BUFFER_CREATE_INFO")

        alloc = Alloc(resource, device_memory, requirements.size)
        self.allocations.append(alloc)

        return weakref.proxy(alloc)

    def shared_alloc(self, size, types):
        _, api, device = self.ctx

        memory_type_index = self._get_memory_type_index(types)

        device_memory = hvk.allocate_memory(api, device, hvk.memory_allocate_info(
            allocation_size = size,
            memory_type_index = memory_type_index
        ))

        alloc = SharedAlloc(device_memory, size)
        self.allocations.append(alloc)

        return weakref.proxy(alloc)

    def free_alloc(self, alloc):
        _, api, device = self.ctx
        hvk.free_memory(api, device, alloc.device_memory)
        self.allocations.remove(alloc)

    def map_alloc(self, alloc, offset=None, size=None):
        engine, api, device = self.ctx
        offset = offset or 0
        size = size or alloc.size

        pointer = hvk.map_memory(api, device, alloc.device_memory, offset, size)
        unmap = lambda: hvk.unmap_memory(api, device, alloc.device_memory)

        return MappedDeviceMemory(alloc, pointer, unmap)

    def get_resource_requirements(self, resource, resource_type):
        _, api, device = self.ctx

        requirements = None
        if resource_type == vk.STRUCTURE_TYPE_IMAGE_CREATE_INFO:
            requirements = hvk.image_memory_requirements(api, device, resource)
        elif resource_type == vk.STRUCTURE_TYPE_BUFFER_CREATE_INFO:
            requirements = hvk.buffer_memory_requirements(api, device, resource)
        else:
            raise ValueError("value of argument \"resource_type\" must be STRUCTURE_TYPE_IMAGE_CREATE_INFO or STRUCTURE_TYPE_BUFFER_CREATE_INFO")

        return requirements

    def _setup_memory_info(self):
        ctx = self.engine
        api, physical_device = ctx.api, ctx.physical_device

        props = hvk.physical_device_memory_properties(api, physical_device)
        types = props.memory_types[:props.memory_type_count]
        heaps = props.memory_heaps[:props.memory_heap_count]

        self.memory_info["memory_types"] = types
        self.memory_info["memory_heaps"] = heaps

    @lru_cache(maxsize=None, typed=False)
    def _get_memory_type_index(self, memory_type_flags):
        memory_types = self.memory_info["memory_types"]

        for type_index, memory_type in enumerate(memory_types):
            memory_type_properties = hvk.MemoryPropertyFlag(memory_type.property_flags)
            for memory_type_flag in memory_type_flags:
                if hvk.MemoryPropertyFlag(memory_type_flag) in memory_type_properties:
                    return type_index

        raise ValueError(f"No memory type matches the requested flags: {memory_type_flags}")

   
class Alloc(object):
    __slots__ = ("resource", "device_memory", "size", "__weakref__")

    def __init__(self, resource, device_memory, size):
        self.resource = resource
        self.device_memory = device_memory
        self.size = size

class SharedAlloc(object):
    __slots__ = ("device_memory", "size", "__weakref__")

    def __init__(self, device_memory, size):
        self.device_memory = device_memory
        self.size = size

class MappedDeviceMemory(object):
    __slots__ = ("alloc", "pointer", "pointer2", "unmap")

    def __init__(self, alloc, pointer, unmap):
        self.alloc = alloc
        self.pointer = pointer
        self.pointer2 = pointer.value
        self.unmap = unmap

    def write_bytes(self, offset, data):
        offset_pointer = self.pointer2 + offset
        memmove(offset_pointer, byref(data), len(data))

    def write_typed_data(self, src, offset):
        dst = (type(src)*1).from_address(self.pointer2 + offset)
        dst[0] = src

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.unmap()
