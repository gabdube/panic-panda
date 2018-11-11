from .. import vk
from .utils import check_ctypes_members, array, array_pointer
from ctypes import byref


def fence_create_info(flags=0):
    return vk.FenceCreateInfo(
        type = vk.STRUCTURE_TYPE_FENCE_CREATE_INFO,
        next = None,
        flags = flags
    )


def create_fence(api, device, info):
    fence = vk.Fence()
    result = api.CreateFence(device, byref(info), None, byref(fence))
    if result != vk.SUCCESS:
        raise RuntimeError("Failed to create fence")

    return fence


def wait_for_fences(api, device, fences, wait_all=True, timeout=-1):
    fences_count = len(fences)
    fences = array(vk.Fence, fences_count, fences)
    result = api.WaitForFences(device, fences_count, array_pointer(fences), wait_all, timeout)

    if result not in (vk.TIMEOUT, vk.SUCCESS):
        raise RuntimeError(f"Failed to wait for fence: {result}")
    
    return result


def reset_fences(api, device, fences):
    fences_count = len(fences)
    fences = array(vk.Fence, fences_count, fences)
    result = api.ResetFences(device, fences_count, array_pointer(fences))

    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to wait for fence: {result}")
    
    return result


def destroy_fence(api, device, fence):
    api.DestroyFence(device, fence, None)


def semaphore_create_info():
    return vk.SemaphoreCreateInfo(
        type = vk.STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO,
        next = None,
        flags = 0
    )


def create_semaphore(api, device, info):
    semaphore = vk.Semaphore(0)
    result = api.CreateSemaphore(device, byref(info), None, byref(semaphore))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to create semaphore: {result}")

    return semaphore


def destroy_semaphore(api, device, semaphore):
    api.DestroySemaphore(device, semaphore, None)
