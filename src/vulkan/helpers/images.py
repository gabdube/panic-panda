from .. import vk
from .utils import check_ctypes_members, array_pointer, array, sequence_to_array
from ctypes import byref, c_uint32


GRAPHICS_DST_STAGE_MASK = {
    vk.ACCESS_SHADER_READ_BIT: vk.PIPELINE_STAGE_FRAGMENT_SHADER_BIT,
    vk.ACCESS_TRANSFER_WRITE_BIT: vk.PIPELINE_STAGE_TRANSFER_BIT
}

COMPUTE_DST_STAGE_MASK = {
    vk.ACCESS_SHADER_READ_BIT: vk.PIPELINE_STAGE_COMPUTE_SHADER_BIT,
    vk.ACCESS_TRANSFER_WRITE_BIT: vk.PIPELINE_STAGE_TRANSFER_BIT
}

def dst_stage_mask_for_access_mask(access_mask, queue_flags=vk.QUEUE_GRAPHICS_BIT):
    f = None
    if queue_flags & vk.QUEUE_GRAPHICS_BIT != 0:
        f = GRAPHICS_DST_STAGE_MASK.get(access_mask)
    elif queue_flags & vk.QUEUE_COMPUTE_BIT != 0:
        f = COMPUTE_DST_STAGE_MASK.get(access_mask)
    else:
        raise ValueError(f"Queue flags {queue_flags} not implemented")
    
    if f is None:
        raise ValueError(f"Access mask {access_mask} for queue flags {queue_flags} is not implemented")

    return f

def component_mapping(**kwargs):
    check_ctypes_members(vk.ComponentMapping, (), kwargs.keys())
    return vk.ComponentMapping(
        r = kwargs.get('r', vk.COMPONENT_SWIZZLE_R),
        g = kwargs.get('g', vk.COMPONENT_SWIZZLE_G),
        b = kwargs.get('b', vk.COMPONENT_SWIZZLE_B),
        a = kwargs.get('a', vk.COMPONENT_SWIZZLE_A),
    )


def image_subresource_range(**kwargs):
    check_ctypes_members(vk.ImageSubresourceRange, (), kwargs.keys())
    return vk.ImageSubresourceRange(
        aspect_mask = kwargs.get('aspect_mask', vk.IMAGE_ASPECT_COLOR_BIT),
        base_mip_level = kwargs.get('base_mip_level', 0),
        level_count = kwargs.get('level_count', 1),
        base_array_layer = kwargs.get('base_array_layer', 0),
        layer_count = kwargs.get('layer_count', 1),
    )


def image_subresource_layers(**kwargs):
    check_ctypes_members(vk.ImageSubresourceLayers, (), kwargs.keys())
    return vk.ImageSubresourceLayers(
        aspect_mask = kwargs.get('aspect_mask', vk.IMAGE_ASPECT_COLOR_BIT),
        mip_level = kwargs.get('mip_level', 0),
        base_array_layer = kwargs.get('base_array_layer', 0),
        layer_count = kwargs.get('layer_count', 1)
    )


def buffer_image_copy(**kwargs):
    check_ctypes_members(vk.BufferImageCopy, ('image_extent', ), kwargs.keys())
    return vk.BufferImageCopy(
        buffer_offset = kwargs.get('buffer_offset', 0),
        buffer_row_length = kwargs.get('buffer_row_length', 0),
        buffer_image_height = kwargs.get('buffer_image_height', 0),
        image_subresource = kwargs.get('image_subresource', image_subresource_layers()),
        image_offset = kwargs.get('image_offset', vk.Offset3D(0, 0, 0)),
        image_extent = kwargs['image_extent']
    )


def image_copy(**kwargs):
    check_ctypes_members(vk.ImageCopy, ('extent', ), kwargs.keys())
    return vk.ImageCopy(
        src_subresource = kwargs.get('src_subresource', image_subresource_layers()),
        src_offset = kwargs.get('src_offset', vk.Offset3D(0, 0, 0)),

        dst_subresource = kwargs.get('dst_subresource', image_subresource_layers()),
        dst_offset = kwargs.get('dst_offset', vk.Offset3D(0, 0, 0)),

        extent = kwargs['extent']
    )


def image_view_create_info(**kwargs):
    check_ctypes_members(vk.ImageViewCreateInfo, ('image', 'format'), kwargs.keys())

    return vk.ImageViewCreateInfo(
        type = vk.STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO,
        next = None,
        flags = 0,
        image = kwargs['image'],
        view_type = kwargs.get('view_type', vk.IMAGE_VIEW_TYPE_2D),
        format = kwargs['format'],
        components = kwargs.get('components', component_mapping()),
        subresource_range = kwargs.get('subresource_range', image_subresource_range())
    )


def create_image_view(api, device, info):
    view = vk.ImageView(0)
    result = api.CreateImageView(device, byref(info), None, byref(view))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to create an image view: {result}")

    return view


def destroy_image_view(api, device, view):
    api.DestroyImageView(device, view, None)


def image_create_info(**kwargs):
    check_ctypes_members(vk.ImageCreateInfo, ('format', 'extent', 'usage'), kwargs.keys())

    queue_family_indices, queue_family_indices_ptr, queue_family_index_count = sequence_to_array(kwargs.get('queue_family_indices'), c_uint32)

    return vk.ImageCreateInfo(
        type = vk.STRUCTURE_TYPE_IMAGE_CREATE_INFO,
        next = None,
        flags = kwargs.get('flags', 0),
        image_type = kwargs.get('image_type', vk.IMAGE_TYPE_2D),
        format = kwargs['format'],
        extent = kwargs['extent'],
        mip_levels = kwargs.get('mip_levels', 1),
        array_layers = kwargs.get('array_layers', 1),
        samples = kwargs.get('samples', vk.SAMPLE_COUNT_1_BIT),
        tiling = kwargs.get('tiling', vk.IMAGE_TILING_OPTIMAL),
        usage = kwargs['usage'],
        sharing_mode = kwargs.get('sharing_mode', vk.SHARING_MODE_EXCLUSIVE),
        queue_family_index_count = queue_family_index_count,
        queue_family_indices = queue_family_indices_ptr,
        initial_layout = kwargs.get('initial_layout', vk.IMAGE_LAYOUT_UNDEFINED)
    )


def image_memory_requirements(api, device, image):
    req = vk.MemoryRequirements()
    api.GetImageMemoryRequirements(device, image, byref(req))
    return req


def bind_image_memory(api, device, image, memory, offset=0):
    result = api.BindImageMemory(device, image, memory, offset)
    if result != vk.SUCCESS:
        raise RuntimeError("Failed to bind memory to image")


def create_image(api, device, info):
    image = vk.Image(0)
    result = api.CreateImage(device, byref(info), None, byref(image))
    if result != vk.SUCCESS:
        raise RuntimeError("Failed to create an image")

    return image


def destroy_image(api, device, image):
    api.DestroyImage(device, image, None)


def sampler_create_info(**kwargs):
    required_args = ('mag_filter', 'min_filter')
    check_ctypes_members(vk.SamplerCreateInfo, required_args, kwargs.keys())
    return vk.SamplerCreateInfo(
        type = vk.STRUCTURE_TYPE_SAMPLER_CREATE_INFO,
        next = None,
        flags = 0,
        mag_filter = kwargs['mag_filter'],
        min_filter = kwargs['min_filter'],
        mipmap_mode = kwargs.get('mipmap_mode', vk.SAMPLER_MIPMAP_MODE_LINEAR),
        address_mode_V = kwargs.get('address_mode_V', vk.SAMPLER_ADDRESS_MODE_REPEAT),
        address_mode_U = kwargs.get('address_mode_U', vk.SAMPLER_ADDRESS_MODE_REPEAT),
        address_mode_W = kwargs.get('address_mode_W', vk.SAMPLER_ADDRESS_MODE_REPEAT),
        mip_lod_bias = kwargs.get('mip_lod_bias', 0.0),
        anisotropy_enable = kwargs.get('anisotropy_enable', vk.FALSE),
        max_anisotropy = kwargs.get('max_anisotropy', 1.0),
        compare_enable = kwargs.get('compare_enable', vk.FALSE),
        compare_op = kwargs.get('compare_op', vk.COMPARE_OP_NEVER),
        min_lod = kwargs.get('min_lod', 0.0),
        max_lod = kwargs.get('max_lod', 0.0),
        border_color = kwargs.get('border_color', vk.BORDER_COLOR_FLOAT_TRANSPARENT_BLACK),
        unnormalized_coordinates = kwargs.get('unnormalized_coordinates', vk.FALSE)
    )


def create_sampler(api, device, info):
    sampler = vk.Sampler(0)
    result = api.CreateSampler(device, byref(info), None, byref(sampler))
    if result != vk.SUCCESS:
        raise RuntimeError("Failed to create a sampler")

    return sampler


def destroy_sampler(api, device, sampler):
    api.DestroySampler(device, sampler, None)
