from .. import vk
from .utils import check_ctypes_members
from ctypes import byref
from enum import IntFlag


class BufferUsageFlags(IntFlag):
    TransferSrc = vk.BUFFER_USAGE_TRANSFER_SRC_BIT
    TransferDst = vk.BUFFER_USAGE_TRANSFER_DST_BIT
    UniformTexelBuffer = vk.BUFFER_USAGE_UNIFORM_TEXEL_BUFFER_BIT
    StorageTexelBuffer = vk.BUFFER_USAGE_STORAGE_TEXEL_BUFFER_BIT
    UniformBuffer = vk.BUFFER_USAGE_UNIFORM_BUFFER_BIT
    StorageBuffer = vk.BUFFER_USAGE_STORAGE_BUFFER_BIT
    IndexBuffer = vk.BUFFER_USAGE_INDEX_BUFFER_BIT
    VertexBuffer = vk.BUFFER_USAGE_VERTEX_BUFFER_BIT
    IndirectBuffer = vk.BUFFER_USAGE_INDIRECT_BUFFER_BIT


def buffer_create_info(**kwargs):
    check_ctypes_members(vk.BufferCreateInfo, ('size', 'usage'), kwargs.keys())
    return vk.BufferCreateInfo(
        type = vk.STRUCTURE_TYPE_BUFFER_CREATE_INFO, 
        next = None, 
        flags = 0,
        size = kwargs['size'],
        usage = kwargs['usage'],
        sharing_mode = kwargs.get('sharing_mode') or vk.SHARING_MODE_EXCLUSIVE,
        queue_family_index_count = kwargs.get('queue_family_index_count') or 0,
        queue_family_indices = kwargs.get('queue_family_indices') or None
    )


def buffer_memory_requirements(api, device, buffer):
    memreq = vk.MemoryRequirements()
    api.GetBufferMemoryRequirements(device, buffer, byref(memreq))
    return memreq


def bind_buffer_memory(api, device, buffer, memory, offset):
    result = api.BindBufferMemory(device, buffer, memory, offset)
    if result != vk.SUCCESS:
        raise RuntimeError('Failed to bind buffer {} to memory {} at offset {}: {}'.format(buffer.value, memory.value, offset, result))


def create_buffer(api, device, info):
    buffer = vk.Buffer(0)
    result = api.CreateBuffer(device, byref(info), None, byref(buffer))
    if result != vk.SUCCESS:
        raise RuntimeError('Failed to create buffer object. Error code: 0x{:X}'.format(result))

    return buffer


def destroy_buffer(api, device, handle):
    api.DestroyBuffer(device, handle, None)
