from .. import vk
from .utils import array, array_pointer, check_ctypes_members, sequence_to_array
from ctypes import c_int32, c_uint32, c_uint64, byref


MAX_ACQUIRE_TIMEOUT = c_uint64(-1).value


def create_win32_surface(api, instance, window):
    info = vk.Win32SurfaceCreateInfoKHR(
        type = vk.STRUCTURE_TYPE_WIN32_SURFACE_CREATE_INFO_KHR,
        next = None,
        flags = 0,
        hinstance = window.module,
        hwnd = window.handle
    )

    surface = vk.SurfaceKHR(0)
    result = api.CreateWin32SurfaceKHR(instance, byref(info), None, byref(surface))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to create the window surface: {result}")

    return surface


def create_xcb_surface(api, instance, window):
    info = vk.XcbSurfaceCreateInfoKHR(
        type = vk.STRUCTURE_TYPE_XCB_SURFACE_CREATE_INFO_KHR,
        next = None,
        flags = 0,
        connection = window.connection,
        window = window.handle
    )

    surface = vk.SurfaceKHR(0)
    result = api.CreateXcbSurfaceKHR(instance, byref(info), None, byref(surface))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to create the window surface: {result}")

    return surface


def destroy_surface(api, instance, surface):
    api.DestroySurfaceKHR(instance, surface, None)

def physical_device_surface_capabilities(api, physical_device, surface):
    caps = vk.SurfaceCapabilitiesKHR()
    result = api.GetPhysicalDeviceSurfaceCapabilitiesKHR(physical_device, surface, byref(caps))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to get surface capabilities: {result}")

    return caps


def physical_device_surface_formats(api, physical_device, surface):
    formats_count = c_uint32(0)

    result = api.GetPhysicalDeviceSurfaceFormatsKHR(physical_device, surface, byref(formats_count), None)
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to get the count of the surface supported formats: {result}")

    formats = array(vk.SurfaceFormatKHR, formats_count.value)()
    result = api.GetPhysicalDeviceSurfaceFormatsKHR(physical_device, surface, formats_count, array_pointer(formats))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to get surface supported formats: {result}")

    return tuple(formats)


def physical_device_surface_present_modes(api, physical_device, surface):
    present_count = c_uint32(0)

    result = api.GetPhysicalDeviceSurfacePresentModesKHR(physical_device, surface, byref(present_count), None)
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to get the count of the surface present modes: {result}")

    present_modes = array(c_uint32, present_count.value)()
    result = api.GetPhysicalDeviceSurfacePresentModesKHR(physical_device, surface, present_count, array_pointer(present_modes))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to get surface supported present modes: {result}")

    return tuple(present_modes)


def get_physical_device_surface_support(api, physical_device, surface, queue_family_index):
    supported = vk.Bool32(0)
    result = api.GetPhysicalDeviceSurfaceSupportKHR(physical_device, queue_family_index, surface, byref(supported))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to get surface support: {result}")

    return supported.value == vk.TRUE
        

def swapchain_images(api, device, swapchain):
    images_count = c_uint32(0)

    result = api.GetSwapchainImagesKHR(device, swapchain, byref(images_count), None)
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to get the number of swapchain images: {result}")

    images = array(vk.Image, images_count.value)()
    result = api.GetSwapchainImagesKHR(device, swapchain, images_count, array_pointer(images))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to get the swapchain images: {result}")

    return tuple(vk.Image(i) for i in images)


def swapchain_create_info(**kwargs):
    required_fields = ('surface', 'image_format', 'image_color_space', 'image_extent')
    check_ctypes_members(vk.SwapchainCreateInfoKHR, required_fields, kwargs.keys())

    queue_family_indices, queue_family_indices_ptr, queue_family_index_count = sequence_to_array(kwargs.get('queue_family_indices'), c_uint32)

    return vk.SwapchainCreateInfoKHR(
        type = vk.STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR,
        next = None, 
        flags = 0,
        surface = kwargs['surface'],
        min_image_count = kwargs.get('min_image_count', 1),
        image_format = kwargs['image_format'],
        image_color_space = kwargs['image_color_space'],
        image_extent = kwargs['image_extent'],
        image_array_layers = kwargs.get('image_array_layers', 1),
        image_usage = kwargs.get('image_usage', vk.IMAGE_USAGE_COLOR_ATTACHMENT_BIT),
        image_sharing_mode = kwargs.get('image_sharing_mode', vk.SHARING_MODE_EXCLUSIVE),
        queue_family_index_count = queue_family_index_count,
        queue_family_indices = queue_family_indices_ptr,
        pre_transform = kwargs.get('pre_transform', vk.SURFACE_TRANSFORM_IDENTITY_BIT_KHR),
        composite_alpha = kwargs.get('composite_alpha', vk.COMPOSITE_ALPHA_OPAQUE_BIT_KHR),
        present_mode = kwargs.get('present_mode', vk.PRESENT_MODE_FIFO_KHR),
        clipped = kwargs.get('clipped', False),
        old_swapchain = kwargs.get('old_swapchain', 0)
    )


def create_swapchain(api, device, info):
    swapchain = vk.SwapchainKHR(0)
    result = api.CreateSwapchainKHR(device, byref(info), None, byref(swapchain))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to create the swapchain: {result}")

    return swapchain


def destroy_swapchain(api, device, swapchain):
    api.DestroySwapchainKHR(device, swapchain, None)


def acquire_next_image(api, device, swapchain, timeout = MAX_ACQUIRE_TIMEOUT, semaphore=0, fence=0):
    image_index = c_uint32(0)
    result = api.AcquireNextImageKHR(device, swapchain, timeout, semaphore, fence, byref(image_index))
    
    result = c_int32(result).value
    if result not in (vk.SUCCESS, vk.ERROR_OUT_OF_DATE_KHR):
        raise RuntimeError(f"Failed to create the acquire next image in the swapchain: {c_int32(result).value}")

    return image_index.value, result


def present_info(**kwargs):
    check_ctypes_members(vk.PresentInfoKHR, ('swapchains', 'image_indices'), kwargs.keys())

    semaphores, semaphores_ptr, semaphore_count = sequence_to_array(kwargs.get('wait_semaphores'), vk.Semaphore)
    swapchains, swapchains_ptr, swapchain_count = sequence_to_array(kwargs['swapchains'], vk.SwapchainKHR)
    image_indices, image_indices_ptr, _ = sequence_to_array(kwargs['image_indices'], c_uint32)

    return vk.PresentInfoKHR(
        type = vk.STRUCTURE_TYPE_PRESENT_INFO_KHR,
        next = None,
        wait_semaphore_count = semaphore_count,
        wait_semaphores = semaphores_ptr,
        swapchain_count = swapchain_count,
        swapchains = swapchains_ptr,
        image_indices = image_indices_ptr,
        results = None
    )

def queue_present(api, queue, info):
    result = api.QueuePresentKHR(queue, byref(info))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to present to swapchain: {result}")


import platform
system_name = platform.system()
if system_name == 'Windows':
    create_surface = create_win32_surface
    SYSTEM_SURFACE_EXTENSION = "VK_KHR_win32_surface"
elif system_name == 'Linux':
    create_surface = create_xcb_surface
    SYSTEM_SURFACE_EXTENSION = "VK_KHR_xcb_surface"
else:
    raise OSError(f"Os \"{system_name}\" is not supported")

del system_name
del platform
