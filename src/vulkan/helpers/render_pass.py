from .. import vk
from .utils import check_ctypes_members, sequence_to_array, array, array_pointer
from ctypes import byref, c_uint32, c_float


def rect_2d(x, y, width, height):
    return vk.Rect2D(
        offset=vk.Offset2D(x=x, y=y),
        extent=vk.Extent2D(width=width, height=height)
    )

def framebuffer_create_info(**kwargs):
    check_ctypes_members(vk.FramebufferCreateInfo, ('render_pass', 'width', 'height', 'attachments'), kwargs.keys())

    attachments, attachments_ptr, attachment_count = sequence_to_array(kwargs['attachments'], vk.ImageView)

    return vk.FramebufferCreateInfo(
        type = vk.STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO,
        next = None, 
        flags = 0,
        render_pass = kwargs['render_pass'],
        attachment_count = attachment_count,
        attachments = attachments_ptr,
        width = kwargs['width'],
        height = kwargs['height'],
        layers = kwargs.get('layers', 1)
    )


def create_framebuffer(api, device, info):
    framebuffer = vk.Framebuffer(0)
    result = api.CreateFramebuffer(device, byref(info), None, byref(framebuffer))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to create a framebuffer: {result}")

    return framebuffer


def destroy_framebuffer(api, device, framebuffer):
    api.DestroyFramebuffer(device, framebuffer, None)


def attachment_description(**kwargs):
    check_ctypes_members(vk.AttachmentDescription, ('format', 'initial_layout'), kwargs.keys())
    return vk.AttachmentDescription(
        flags = kwargs.get('flags', 0),
        format = kwargs['format'],
        samples = kwargs.get('samples', vk.SAMPLE_COUNT_1_BIT),
        load_op = kwargs.get('load_op', vk.ATTACHMENT_LOAD_OP_CLEAR),
        store_op = kwargs.get('store_op', vk.ATTACHMENT_STORE_OP_STORE),
        stencil_load_op = kwargs.get('stencil_load_op', vk.ATTACHMENT_LOAD_OP_DONT_CARE),
        stencil_store_op = kwargs.get('stencil_store_op', vk.ATTACHMENT_STORE_OP_DONT_CARE),
        initial_layout = kwargs['initial_layout'],
        final_layout = kwargs.get('final_layout', kwargs['initial_layout'])
    )


def subpass_description(**kwargs):
    check_ctypes_members(vk.SubpassDescription, ('pipeline_bind_point',), kwargs.keys())

    inputs, inputs_ptr, input_count = sequence_to_array(kwargs.get('input_attachments'), vk.AttachmentReference)
    colors, colors_ptr, color_count = sequence_to_array(kwargs.get('color_attachments'), vk.AttachmentReference)
    resolve, resolve_ptr, _ = sequence_to_array(kwargs.get('resolve_attachments'), vk.AttachmentReference)
    preserve, preserve_ptr, preserve_count = sequence_to_array(kwargs.get('preserve_attachments'), c_uint32)

    depth_stencil, depth_stencil_ptr = kwargs.get('depth_stencil_attachment'), None
    if depth_stencil is not None:
        depth_stencil = array(vk.AttachmentReference, 1, (depth_stencil,))
        depth_stencil_ptr = array_pointer(depth_stencil)

    return vk.SubpassDescription(
        flags = kwargs.get('flags', 0),
        pipeline_bind_point = kwargs['pipeline_bind_point'],
        input_attachment_count = input_count,
        input_attachments = inputs_ptr,
        color_attachment_count = color_count,
        color_attachments = colors_ptr,
        resolve_attachments = resolve_ptr,
        depth_stencil_attachment = depth_stencil_ptr,
        preserve_attachment_count = preserve_count,
        preserve_attachments = preserve_ptr
    )


def clear_value(color=None, depth=None, stencil=None):
    if color is not None:
        color = array(c_float, 4, color)
        return vk.ClearValue(color = vk.ClearColorValue(color))
    else:
        return vk.ClearValue(depth_stencil = vk.ClearDepthStencilValue(depth=depth, stencil=stencil))


def subpass_dependency(**kwargs):
    required_args = ('src_subpass', 'dst_subpass', 'src_stage_mask', 'dst_stage_mask', 'src_access_mask', 'dst_access_mask')
    check_ctypes_members(vk.SubpassDependency, required_args, kwargs.keys())
    return vk.SubpassDependency(
        src_subpass = kwargs['src_subpass'],
        dst_subpass = kwargs['dst_subpass'],
        src_stage_mask = kwargs['src_stage_mask'],
        dst_stage_mask = kwargs['dst_stage_mask'],
        src_access_mask = kwargs['src_access_mask'],
        dst_access_mask = kwargs['dst_access_mask'],
        dependency_flags = kwargs.get('dependency_flags', vk.DEPENDENCY_BY_REGION_BIT)
    )


def render_pass_begin_info(**kwargs):
    required_args = ('render_pass', 'framebuffer', 'render_area')
    check_ctypes_members(vk.RenderPassBeginInfo, required_args, kwargs.keys())

    clear_values, clear_values_ptr, clear_value_count = sequence_to_array(kwargs.get('clear_values'), vk.ClearValue)

    return vk.RenderPassBeginInfo(
        type = vk.STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO,
        next = None,
        render_pass = kwargs['render_pass'],
        framebuffer = kwargs['framebuffer'],
        render_area = kwargs['render_area'],
        clear_value_count = clear_value_count,
        clear_values = clear_values_ptr
    )


def render_pass_create_info(**kwargs):
    check_ctypes_members(vk.RenderPassCreateInfo, ('subpasses',), kwargs.keys())

    attachments, attachments_ptr, attachment_count = sequence_to_array(kwargs.get('attachments'), vk.AttachmentDescription)
    dependencies, dependencies_ptr, dependency_count = sequence_to_array(kwargs.get('dependencies'), vk.SubpassDependency)
    subpasses, subpasses_ptr, subpass_count = sequence_to_array(kwargs['subpasses'], vk.SubpassDescription)

    return vk.RenderPassCreateInfo(
        type = vk.STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO,
        next = None,
        flags = 0,
        attachment_count = attachment_count,
        attachments = attachments_ptr,
        subpass_count = subpass_count,
        subpasses = subpasses_ptr,
        dependency_count = dependency_count,
        dependencies = dependencies_ptr
    )


def create_render_pass(api, device, info):
    render_pass = vk.RenderPass(0)
    result = api.CreateRenderPass(device, byref(info), None, byref(render_pass))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to create a renderpass: {result}")

    return render_pass


def destroy_render_pass(api, device, render_pass):
    api.DestroyRenderPass(device, render_pass, None)
