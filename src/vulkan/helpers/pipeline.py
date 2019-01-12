from .. import vk
from .utils import check_ctypes_members, sequence_to_array, array, array_pointer
from ctypes import byref, c_char_p, c_float, pointer, c_int


def pipeline_cache_create_info(**kwargs):
    check_ctypes_members(vk.PipelineCacheCreateInfo, (), kwargs.keys())
    return vk.PipelineCacheCreateInfo(
        type = vk.STRUCTURE_TYPE_PIPELINE_CACHE_CREATE_INFO,
        next = None,
        flags = 0,
        initial_data_size = kwargs.get('initial_data_size', 0),
        initial_data = kwargs.get('initial_data')
    )


def create_pipeline_cache(api, device, info):
    cache = vk.PipelineCache(0)
    result = api.CreatePipelineCache(device, byref(info), None, byref(cache))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to create a pipeline cache: {result}")

    return cache


def destroy_pipeline_cache(api, device, pipeline_cache):
    api.DestroyPipelineCache(device, pipeline_cache, None)


def pipeline_layout_create_info(**kwargs):
    check_ctypes_members(vk.PipelineLayoutCreateInfo, ('set_layouts',), kwargs.keys())

    set_layouts, set_layouts_ptr, set_layout_count = sequence_to_array(kwargs['set_layouts'], vk.DescriptorSetLayout)
    push_constants, push_constants_ptr, push_constant_count = sequence_to_array(kwargs.get('push_constant_ranges'), vk.DescriptorSetLayout)

    return vk.PipelineLayoutCreateInfo(
        type = vk.STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
        next = None,
        flags = kwargs.get('flags', 0),
        set_layout_count = set_layout_count,
        set_layouts = set_layouts_ptr,
        push_constant_range_count = push_constant_count,
        push_constant_ranges = push_constants_ptr
    )


def create_pipeline_layout(api, device, info):
    layout = vk.PipelineLayout(0)
    result = api.CreatePipelineLayout(device, byref(info), None, byref(layout))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to create a pipeline cache: {result}")

    return layout


def destroy_pipeline_layout(api, device, pipeline_layout):
    api.DestroyPipelineLayout(device, pipeline_layout, None)


def pipeline_shader_stage_create_info(**kwargs):
    check_ctypes_members(vk.PipelineShaderStageCreateInfo, ('stage', 'module'), kwargs.keys())

    name = bytes(kwargs.get('name', 'main'), 'utf-8') + b'\x00'
    name = c_char_p(name)

    specialization_info = kwargs.get('specialization_info')
    if specialization_info is not None and not hasattr(specialization_info, 'contents'):
        specialization_info = pointer(specialization_info)

    return vk.PipelineShaderStageCreateInfo(
        type = vk.STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
        next = None,
        flags = kwargs.get('flags', 0),
        stage = kwargs['stage'],
        module = kwargs['module'],
        name = name,
        specialization_info = specialization_info
    )


def pipeline_vertex_input_state_create_info(**kwargs):
    required_arguments = ('vertex_binding_descriptions', 'vertex_attribute_descriptions')
    check_ctypes_members(vk.PipelineVertexInputStateCreateInfo, required_arguments, kwargs.keys())

    vbd, vbd_ptr, vbd_count = sequence_to_array(kwargs['vertex_binding_descriptions'], vk.VertexInputBindingDescription)
    vad, vad_ptr, vad_count = sequence_to_array(kwargs['vertex_attribute_descriptions'], vk.VertexInputAttributeDescription)

    return vk.PipelineVertexInputStateCreateInfo(
        type = vk.STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO,
        next = None,
        flags = kwargs.get('flags', 0),
        vertex_binding_description_count = vbd_count,
        vertex_binding_descriptions = vbd_ptr,
        vertex_attribute_description_count = vad_count,
        vertex_attribute_descriptions = vad_ptr
    )


def pipeline_input_assembly_state_create_info(**kwargs):
    check_ctypes_members(vk.PipelineInputAssemblyStateCreateInfo, (), kwargs.keys())

    return vk.PipelineInputAssemblyStateCreateInfo(
        type = vk.STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO,
        next = None,
        flags = kwargs.get('flags', 0),
        topology = kwargs.get('topology', vk.PRIMITIVE_TOPOLOGY_TRIANGLE_LIST),
        primitive_restart_enable = kwargs.get('primitive_restart_enable', vk.FALSE)
    )


def pipeline_viewport_state_create_info(**kwargs):
    check_ctypes_members(vk.PipelineViewportStateCreateInfo, (), kwargs.keys())

    keys = tuple(kwargs.keys())
    viewport_count = scissor_count = 0
    viewports_ptr = scissors_ptr = None
    
    if 'viewport_count' in keys:
        viewport_count = kwargs['viewport_count']
    else:
        viewport_count, viewports_ptr, viewport_count = sequence_to_array(kwargs.get('viewports'), vk.Viewport)

    if 'scissor_count' in keys:
        scissor_count = kwargs['scissor_count']
    else:
        scissors, scissors_ptr, scissor_count = sequence_to_array(kwargs.get('scissors'), vk.Rect2D)

    return vk.PipelineViewportStateCreateInfo(
        type = vk.STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO,
        next = None,
        flags = kwargs.get('flags', 0),
        viewport_count = viewport_count,
        viewports = viewports_ptr,
        scissor_count = scissor_count,
        scissors = scissors_ptr
    )


def pipeline_rasterization_state_create_info(**kwargs):
    check_ctypes_members(vk.PipelineRasterizationStateCreateInfo, (), kwargs.keys())
    return vk.PipelineRasterizationStateCreateInfo(
        type = vk.STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO,
        next = None,
        flags = kwargs.get('flags', 0),
        depth_clamp_enable = kwargs.get('depth_clamp_enabled', vk.FALSE),
        rasterizer_discard_enable = kwargs.get('rasterizer_discard_enable', vk.FALSE),
        polygon_mode = kwargs.get('polygon_mode', vk.POLYGON_MODE_FILL),
        cull_mode = kwargs.get('cull_mode', vk.CULL_MODE_NONE),
        front_face = kwargs.get('front_face', vk.FRONT_FACE_CLOCKWISE),
        depth_bias_enable = kwargs.get('depth_bias_enable', vk.FALSE),
        depth_bias_constant_factor = kwargs.get('depth_bias_constant_factor', 0),
        depth_bias_clamp = kwargs.get('depth_bias_clamp', 0.0),
        depth_bias_slope_factor = kwargs.get('depth_bias_slope_factor', 0.0),
        line_width = kwargs.get('line_width', 1.0),
    )


def pipeline_multisample_state_create_info(**kwargs):
    check_ctypes_members(vk.PipelineMultisampleStateCreateInfo, (), kwargs.keys())
    return vk.PipelineMultisampleStateCreateInfo(
        type = vk.STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO,
        next = None,
        flags = kwargs.get('flags', 0),
        rasterization_samples = kwargs.get('rasterization_samples', vk.SAMPLE_COUNT_1_BIT),
        sample_shading_enable = kwargs.get('sample_shading_enable', vk.FALSE),
        min_sample_shading = kwargs.get('sample_shading_enable', 0.0),
        sample_mask = kwargs.get('sample_mask'),
        alpha_toCoverage_enable = kwargs.get('alpha_toCoverage_enable', vk.FALSE),
        alpha_toOne_enable = kwargs.get('alpha_toOne_enable', vk.FALSE)
    )


def stencil_op_state(**kwargs):
    check_ctypes_members(vk.StencilOpState, (), kwargs.keys())
    return vk.StencilOpState(
        fail_op = vk.STENCIL_OP_KEEP,
        pass_op = vk.STENCIL_OP_KEEP,
        depth_fail_op = vk.STENCIL_OP_KEEP,
        compare_op = vk.COMPARE_OP_ALWAYS,
        compare_mask = vk.STENCIL_OP_KEEP,
        write_mask =vk.STENCIL_OP_KEEP,
        reference = vk.STENCIL_OP_KEEP
    )


def pipeline_depth_stencil_state_create_info(**kwargs):
    check_ctypes_members(vk.PipelineDepthStencilStateCreateInfo, (), kwargs.keys())

    return vk.PipelineDepthStencilStateCreateInfo(
        type = vk.STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO,
        next = None,
        flags = kwargs.get('flags', 0),
        depth_test_enable = kwargs.get('depth_test_enable', vk.FALSE),
        depth_write_enable = kwargs.get('depth_write_enable', vk.FALSE),
        depth_compare_op = kwargs.get('depth_compare_op', 0), 
        depth_bounds_test_enable = kwargs.get('depth_bounds_test_enable', vk.FALSE), 
        stencil_test_enable = kwargs.get('stencil_test_enable', vk.FALSE), 
        front = kwargs.get('front', stencil_op_state()), 
        back = kwargs.get('back', stencil_op_state()), 
        min_depth_bounds = kwargs.get('min_depth_bounds', 0.0), 
        max_depth_bounds = kwargs.get('max_depth_bounds', 1.0), 
    )


def pipeline_color_blend_attachment_state(**kwargs):
    check_ctypes_members(vk.PipelineColorBlendAttachmentState, (), kwargs.keys())
    return vk.PipelineColorBlendAttachmentState(
        blend_enable = vk.FALSE,
        src_color_blend_factor = 0,
        dst_color_blend_factor = 0,
        color_blend_op = 0,
        src_alpha_blend_factor = 0,
        dst_alpha_blend_factor = 0,
        alpha_blend_op = 0,
        color_write_mask = 0xF
    )


def pipeline_color_blend_state_create_info(**kwargs):
    check_ctypes_members(vk.PipelineColorBlendStateCreateInfo, ('attachments',), kwargs.keys())

    attachments, attachments_ptr, attachment_count = sequence_to_array(kwargs['attachments'], vk.PipelineColorBlendAttachmentState)

    return vk.PipelineColorBlendStateCreateInfo(
        type = vk.STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO,
        next = None,
        flags = kwargs.get('flags', 0),
        logic_opEnable = kwargs.get('logic_op_enable', False),
        logic_op = kwargs.get('logic_op', 0),
        attachment_count = attachment_count,
        attachments = attachments_ptr,
        blend_constants = kwargs.get('blend_constants', array(c_float, 4, (0,0,0,0)))
    )


def pipeline_dynamic_state_create_info(**kwargs):
    check_ctypes_members(vk.PipelineDynamicStateCreateInfo, ('dynamic_states',), kwargs.keys())

    dynamic_states, dynamic_states_ptr, dynamic_state_count = sequence_to_array(kwargs['dynamic_states'], vk.DynamicState)

    return vk.PipelineDynamicStateCreateInfo(
        type = vk.STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO,
        next = None,
        flags = 0,
        dynamic_state_count = dynamic_state_count,
        dynamic_states = dynamic_states_ptr
    )


def graphics_pipeline_create_info(**kwargs):

    def refptr(obj_name):
        obj, obj_ref =  kwargs.get(obj_name), None
        if obj is not None:
            obj_ref = pointer(obj)
        return obj, obj_ref

    required_fields = ('stages', 'vertex_input_state', 'input_assembly_state', 'rasterization_state', 'layout', 'render_pass')
    check_ctypes_members(vk.GraphicsPipelineCreateInfo, required_fields, kwargs.keys())

    stages, stages_ptr, stage_count = sequence_to_array(kwargs['stages'], vk.PipelineShaderStageCreateInfo)
    tessellation_state, tessellation_state_ptr = refptr('tessellation_state')
    viewport_state, viewport_state_ptr = refptr('viewport_state')
    multisample_state, multisample_state_ptr = refptr('multisample_state')
    depth_stencil_state, depth_stencil_state_ptr = refptr('depth_stencil_state')
    color_blend_state, color_blend_state_ptr = refptr('color_blend_state')
    dynamic_state, dynamic_state_ptr = refptr('dynamic_state')

    return vk.GraphicsPipelineCreateInfo(
        type = vk.STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO,
        next = None,
        flags = kwargs.get('flags', 0),
        stage_count = stage_count,
        stages = stages_ptr,
        vertex_input_state = pointer(kwargs['vertex_input_state']),
        input_assembly_state = pointer(kwargs['input_assembly_state']),
        tessellation_state = tessellation_state_ptr,
        viewport_state = viewport_state_ptr,
        rasterization_state = pointer(kwargs['rasterization_state']),
        multisample_state = multisample_state_ptr,
        depth_stencil_state = depth_stencil_state_ptr,
        color_blend_state = color_blend_state_ptr,
        dynamic_state = dynamic_state_ptr,
        layout = kwargs['layout'],
        render_pass = kwargs['render_pass'],
        subpass = kwargs.get('subpass', 0),
        base_pipeline_handle = kwargs.get('base_pipeline_handle', vk.Pipeline(0)),
        base_pipeline_index = kwargs.get('base_pipeline_index', 0)
    )


def create_graphics_pipelines(api, device, infos, cache=0):
    infos, infos_ptr, infos_count = sequence_to_array(infos, vk.GraphicsPipelineCreateInfo)
    pipelines = array(vk.Pipeline, infos_count)()

    result = api.CreateGraphicsPipelines(device, cache, infos_count, infos_ptr, None, array_pointer(pipelines))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to create graphics pipeline: {result}")
    
    return tuple(vk.Pipeline(p) for p in pipelines)


def compute_pipeline_create_info(**kwargs):
    required_fields = ('stage', 'layout')
    check_ctypes_members(vk.ComputePipelineCreateInfo, required_fields, kwargs.keys())

    return vk.ComputePipelineCreateInfo(
        type = vk.STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO,
        next = None,
        flags = 0,
        stage = kwargs['stage'],
        layout = kwargs['layout'],
        base_pipeline_handle = kwargs.get('base_pipeline_handle', 0),
        base_pipeline_index = kwargs.get('base_pipeline_index', -1)
    )


def create_compute_pipelines(api, device, infos, cache = 0):
    infos, infos_ptr, infos_count = sequence_to_array(infos, vk.ComputePipelineCreateInfo)
    pipelines = array(vk.Pipeline, infos_count)()

    result = api.CreateComputePipelines(device, cache, infos_count, infos_ptr, None, array_pointer(pipelines))
    if result != vk.SUCCESS:
        raise RuntimeError(f"Failed to create compute pipeline: {c_int(result)}")
    
    return tuple(vk.Pipeline(p) for p in pipelines)


def destroy_pipeline(api, device, pipeline):
    api.DestroyPipeline(device, pipeline, None)
