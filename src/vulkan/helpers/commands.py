from .. import vk
from .utils import check_ctypes_members, array, array_pointer, sequence_to_array
from .images import image_subresource_range
from ctypes import byref, pointer, c_uint32, c_int32
        

def command_pool_create_info(**kwargs):
    check_ctypes_members(vk.CommandPoolCreateInfo, ('queue_family_index',), kwargs.keys())
    return vk.CommandPoolCreateInfo(
        type = vk.STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
        next = None,
        flags = kwargs.get('flags') or 0,
        queue_family_index = kwargs['queue_family_index']
    )


def create_command_pool(api, device, info):
    pool = vk.CommandPool(0)
    result = api.CreateCommandPool(device, byref(info), None, byref(pool))
    if result != vk.SUCCESS:
        raise RuntimeError("Failed to create command pool: {}".format(result))
    return pool


def destroy_command_pool(api, device, pool):
    api.DestroyCommandPool(device, pool, None)


def command_buffer_allocate_info(**kwargs):
    check_ctypes_members(vk.CommandBufferAllocateInfo, ('command_pool', 'command_buffer_count'), kwargs.keys())
    return vk.CommandBufferAllocateInfo(
        type = vk.STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
        next = None,
        command_pool = kwargs['command_pool'],
        level = kwargs.get('level') or 0,
        command_buffer_count = kwargs['command_buffer_count']
    )


def allocate_command_buffers(api, device, info):
    buffers = array(vk.CommandBuffer, info.command_buffer_count)()
    result = api.AllocateCommandBuffers(device, byref(info), array_pointer(buffers))
    if result != vk.SUCCESS:
        raise RuntimeError("Failed to allocate command buffers")

    return tuple(vk.CommandBuffer(b) for b in buffers)


def command_buffer_inheritance_info(**kwargs):
    check_ctypes_members(vk.CommandBufferInheritanceInfo, (), kwargs.keys())
    return vk.CommandBufferInheritanceInfo(
        type = vk.STRUCTURE_TYPE_COMMAND_BUFFER_INHERITANCE_INFO,
        next = None,
        render_pass = kwargs.get('render_pass', 0),
        subpass = kwargs.get('subpass', 0),
        framebuffer = kwargs.get('framebuffer', 0),
        occlusion_query_enable = kwargs.get('occlusion_query_enable', 0),
        query_flags = kwargs.get('query_flags', 0),
        pipeline_statistics = kwargs.get('pipeline_statistics', 0)
    )


def command_buffer_begin_info(**kwargs):
    check_ctypes_members(vk.CommandBufferBeginInfo, (), kwargs.keys())

    inheritance_info = kwargs.get('inheritance_info')
    if inheritance_info is not None:
        inheritance_info = pointer(inheritance_info)

    return vk.CommandBufferBeginInfo(
        type = vk.STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
        next = None,
        flags = kwargs.get('flags') or 0,
        inheritance_info = inheritance_info
    )


def begin_command_buffer(api, cmd, info):
    result = api.BeginCommandBuffer(cmd, byref(info))
    if result != vk.SUCCESS:
        raise RuntimeError("Could not begin recording to command buffer {}: {}".format(cmd.value, result))


def end_command_buffer(api, cmd):
    api.EndCommandBuffer(cmd)


def image_memory_barrier(**kwargs):
    required_members = ('dst_access_mask', 'new_layout', 'image')
    check_ctypes_members(vk.ImageMemoryBarrier, required_members, kwargs.keys())
    return vk.ImageMemoryBarrier(
        type = vk.STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER,
        next = None,
        src_access_mask = kwargs.get('src_access_mask', 0),
        dst_access_mask = kwargs['dst_access_mask'],
        old_layout = kwargs.get('old_layout', vk.IMAGE_LAYOUT_UNDEFINED),
        new_layout = kwargs['new_layout'],
        src_queue_family_index = kwargs.get('src_queue_family_index', vk.QUEUE_FAMILY_IGNORED),
        dst_queue_family_index = kwargs.get('dst_queue_family_index', vk.QUEUE_FAMILY_IGNORED),
        image = kwargs['image'],
        subresource_range = kwargs.get('subresource_range', image_subresource_range())
    )


def pipeline_barrier(api, cmd, barriers, src_stage_mask=vk.PIPELINE_STAGE_ALL_COMMANDS_BIT, dst_stage_mask=vk.PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, dependency_flags=0):
  
    mb, bb, ib = vk.MemoryBarrier, vk.BufferMemoryBarrier, vk.ImageMemoryBarrier

    memory_barriers, buffer_barriers, image_barriers = [], [], []
    for barrier in barriers:
        tb = type(barrier)
        if tb is mb: memory_barriers.append(barrier)
        elif tb is bb: buffer_barriers.append(barrier)
        elif tb is ib: image_barriers.append(barrier)
        else: 
            raise ValueError(f"Barriers type must one of those types: (MemoryBarrier, BufferMemoryBarrier, ImageMemoryBarrier), got {tb.__qualname__}")

    memory_barriers, memory_barriers_ptr, memory_barriers_count = sequence_to_array(memory_barriers, vk.MemoryBarrier)
    buffer_barriers, buffer_barriers_ptr, buffer_barriers_count = sequence_to_array(buffer_barriers, vk.BufferMemoryBarrier)
    image_barriers, image_barriers_ptr, image_barriers_count = sequence_to_array(image_barriers, vk.ImageMemoryBarrier)

    api.CmdPipelineBarrier(
        cmd, 
        src_stage_mask, 
        dst_stage_mask, 
        dependency_flags,
        memory_barriers_count, memory_barriers_ptr,
        buffer_barriers_count, buffer_barriers_ptr,
        image_barriers_count, image_barriers_ptr
    )


def begin_render_pass(api, cmd, info, contents):
    api.CmdBeginRenderPass(cmd, byref(info), contents)


def end_render_pass(api, cmd):
    api.CmdEndRenderPass(cmd)


def viewport(**kwargs):
    check_ctypes_members(vk.Viewport, ('width', 'height'), kwargs.keys())
    return vk.Viewport(
        x = kwargs.get('x', 0),
        y = kwargs.get('y', 0),
        width = kwargs['width'],
        height = kwargs['height'],
        min_depth = kwargs.get('min_depth', 0.0),
        max_depth = kwargs.get('max_depth', 1.0),
    )


def set_viewport(api, cmd, viewports, first_viewport=0):
    viewports, viewports_ptr, viewport_count = sequence_to_array(viewports, vk.Viewport)
    api.CmdSetViewport(cmd, first_viewport, viewport_count, viewports_ptr)


def set_scissor(api, cmd, scissors, first_scissor=0):
    scissors, scissors_ptr, scissor_count = sequence_to_array(scissors, vk.Rect2D)
    api.CmdSetScissor(cmd, first_scissor, scissor_count, scissors_ptr)


def copy_buffer(api, cmd, src_buffer, dst_buffer, regions):
    regions, regions_ptr, region_count = sequence_to_array(regions, vk.BufferCopy)
    api.CmdCopyBuffer(cmd, src_buffer, dst_buffer, region_count, regions_ptr)


def copy_buffer_to_image(api, cmd, src_buffer, dst_image, dst_image_layout, regions):
    regions, regions_ptr, region_count = sequence_to_array(regions, vk.BufferImageCopy)
    api.CmdCopyBufferToImage(cmd, src_buffer, dst_image, dst_image_layout, region_count, regions_ptr)


def copy_image(api, cmd, src_image, src_image_layout, dst_image, dst_image_layout, regions):
    regions, regions_ptr, region_count = sequence_to_array(regions, vk.ImageCopy)
    api.CmdCopyImage(cmd, src_image, src_image_layout, dst_image, dst_image_layout, region_count, regions_ptr)


def execute_commands(api, cmd, sub_buffers):
    sub_buffers, sub_buffers_ptr, sub_buffer_count = sequence_to_array(sub_buffers, vk.CommandBuffer)
    api.CmdCopyImage(cmd, sub_buffer_count, sub_buffers_ptr) 


def clear_attachments(api, cmd, attachments, regions):
    attachments, attachments_ptr, attachment_count = sequence_to_array(attachments, vk.ClearAttachment)
    regions, regions_ptr, region_count = sequence_to_array(regions, vk.ClearRect)

    api.CmdClearAttachments(cmd, attachment_count, attachments_ptr, region_count, regions_ptr) 


def bind_pipeline(api, cmd, pipeline, bind_point):
    api.CmdBindPipeline(cmd, bind_point, pipeline)


def bind_index_buffer(api, cmd, index_buffer, offset, index_type):
    api.CmdBindIndexBuffer(cmd, index_buffer, offset, index_type)


def bind_vertex_buffers(api, cmd, vertex_buffers, offsets, first_binding=0):
    vbuffers, vbuffers_ptr, vbuffers_count = sequence_to_array(vertex_buffers, vk.Buffer)
    offsets, offsets_ptr, _ = sequence_to_array(offsets, vk.Buffer)
    api.CmdBindVertexBuffers(cmd, first_binding, vbuffers_count, vbuffers_ptr, offsets_ptr)


def draw_indexed(api, cmd, index_count, instance_count=1, first_index=0, vertex_offset=0, first_instance=1):
    api.CmdDrawIndexed(
        cmd,
        index_count, instance_count,
        first_index,
        vertex_offset,
        first_instance
    )


def dispatch(api, cmd, x, y, z):
    api.CmdDispatch(cmd, x, y, z)


def bind_descriptor_sets(api, cmd, pipeline_bind_point, layout, descriptor_sets, dynamic_offsets=None, firstSet=0):

    descriptor_sets, descriptor_sets_ptr, descriptor_set_count = sequence_to_array(descriptor_sets, vk.DescriptorSet)
    dynamic_offsets, dynamic_offsets_ptr, dynamic_offset_count = sequence_to_array(dynamic_offsets, c_uint32)

    api.CmdBindDescriptorSets(
        cmd,
        pipeline_bind_point,
        layout,
        firstSet,
        descriptor_set_count,
        descriptor_sets_ptr,
        dynamic_offset_count,
        dynamic_offsets_ptr
    )

def submit_info(**kwargs):
    check_ctypes_members(vk.SubmitInfo, ('command_buffers',), kwargs.keys())

    wait_semaphores, wait_semaphores_ptr, wait_semaphore_count = sequence_to_array(kwargs.get('wait_semaphores'), vk.Semaphore)
    wait_dst_stage_mask, wait_dst_stage_mask_ptr, _ = sequence_to_array(kwargs.get('wait_dst_stage_mask'), vk.PipelineStageFlags)

    signal_semaphores, signal_semaphores_ptr, signal_semaphore_count = sequence_to_array(kwargs.get('signal_semaphores'), vk.Semaphore)

    command_buffers, command_buffers_ptr, command_buffer_count = sequence_to_array(kwargs['command_buffers'], vk.CommandBuffer)

    return vk.SubmitInfo(
        type = vk.STRUCTURE_TYPE_SUBMIT_INFO,
        next = None,
        wait_semaphore_count = wait_semaphore_count,
        wait_semaphores = wait_semaphores_ptr,
        wait_dst_stage_mask = wait_dst_stage_mask_ptr,
        command_buffer_count = command_buffer_count,
        command_buffers = command_buffers_ptr,
        signal_semaphore_count = signal_semaphore_count,
        signal_semaphores = signal_semaphores_ptr
    )


def queue_submit(api, queue, submit_info, fence=vk.Fence(0)):
    submit_count = len(submit_info)
    submits = array(vk.SubmitInfo, submit_count, submit_info)

    result = api.QueueSubmit(queue, submit_count, array_pointer(submits), fence)

    if result != vk.SUCCESS:
        raise RuntimeError("Queue submit failed: {}".format(c_int32(result)))
