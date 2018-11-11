from .. import vk
from .utils import check_ctypes_members, sequence_to_array, array, array_pointer
from ctypes import byref, c_uint32, c_uint8


def descriptor_set_layout_binding(**kwargs):
    required_args = ('binding', 'descriptor_type', 'descriptor_count', 'stage_flags')
    check_ctypes_members(vk.DescriptorSetLayoutBinding, required_args, kwargs.keys())

    samplers, samplers_ptr, _ = sequence_to_array(kwargs.get('immutable_samplers'), vk.Sampler)

    return vk.DescriptorSetLayoutBinding(
        binding = kwargs['binding'],
        descriptor_type = kwargs['descriptor_type'],
        descriptor_count = kwargs['descriptor_count'],
        stage_flags = kwargs['stage_flags'],
        immutable_samplers = samplers_ptr
    )


def vertex_input_binding_description(**kwargs):
    check_ctypes_members(vk.VertexInputBindingDescription, ('binding', 'stride'), kwargs.keys())

    return vk.VertexInputBindingDescription(
        binding = kwargs['binding'],
        stride = kwargs['stride'],
        input_rate = kwargs.get('input_rate', vk.VERTEX_INPUT_RATE_VERTEX)
    )


def vertex_input_attribute_description(**kwargs):
    required_args = ('location', 'binding', 'format', 'offset')
    check_ctypes_members(vk.VertexInputAttributeDescription, required_args, kwargs.keys())

    return vk.VertexInputAttributeDescription(
        location = kwargs['location'],
        binding = kwargs['binding'],
        format = kwargs['format'],
        offset = kwargs['offset']
    )


def descriptor_set_layout_create_info(**kwargs):
    check_ctypes_members(vk.DescriptorSetLayoutCreateInfo, ('bindings',), kwargs.keys())

    bindings, bindings_ptr, binding_count = sequence_to_array(kwargs['bindings'], vk.DescriptorSetLayoutBinding)

    return vk.DescriptorSetLayoutCreateInfo(
        type = vk.STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
        next = None,
        flags = kwargs.get('flags', 0),
        binding_count = binding_count,
        bindings = bindings_ptr
    )

def create_descriptor_set_layout(api, device, info):
    layout = vk.DescriptorSetLayout(0)
    result = api.CreateDescriptorSetLayout(device, byref(info), None, byref(layout))
    if result != vk.SUCCESS:
        raise RuntimeError("Failed to create a descriptor layout")

    return layout


def destroy_descriptor_set_layout(api, device, layout):
    api.DestroyDescriptorSetLayout(device, layout, None)


def shader_module_create_info(**kwargs):
    check_ctypes_members(vk.ShaderModuleCreateInfo, ('code',), kwargs.keys())

    code = kwargs['code']
    code_size = len(code)
    code = array(c_uint8, code_size, code)

    return vk.ShaderModuleCreateInfo(
        type = vk.STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
        next = None,
        flags = kwargs.get('flags', 0),
        code_size = code_size,
        code = array_pointer(code, c_uint32)
    )


def create_shader_module(api, device, info):
    shader = vk.ShaderModule(0)
    result = api.CreateShaderModule(device, byref(info), None, byref(shader))
    if result != vk.SUCCESS:
        raise RuntimeError("Failed to create shader module")

    return shader


def destroy_shader_module(api, device, shader):
    api.DestroyShaderModule(device, shader, None)


def descriptor_pool_create_info(**kwargs):
    check_ctypes_members(vk.DescriptorPoolCreateInfo, ('max_sets', 'pool_sizes'), kwargs.keys())

    pool_sizes, pool_sizes_ptr, pool_size_count = sequence_to_array(kwargs['pool_sizes'], vk.DescriptorPoolSize)

    return vk.DescriptorPoolCreateInfo(
        type = vk.STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
        next = None,
        flags = kwargs.get('flags', 0),
        max_sets = kwargs['max_sets'],
        pool_size_count = pool_size_count,
        pool_sizes = pool_sizes_ptr
    )


def create_descriptor_pool(api, device, info):
    pool = vk.DescriptorPool(0)
    result = api.CreateDescriptorPool(device, byref(info), None, byref(pool))
    if result != vk.SUCCESS:
        raise RuntimeError("Failed to create descriptor pool")

    return pool 


def destroy_descriptor_pool(api, device, pool):
    api.DestroyDescriptorPool(device, pool, None)


def descriptor_set_allocate_info(**kwargs):
    required_arguments = ('descriptor_pool', 'set_layouts')
    check_ctypes_members(vk.DescriptorSetAllocateInfo, required_arguments, kwargs.keys())

    set_layouts, set_layouts_ptr, descriptor_set_count = sequence_to_array(kwargs['set_layouts'], vk.DescriptorSet)

    return vk.DescriptorSetAllocateInfo(
        type = vk.STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
        next = None,
        descriptor_pool = kwargs['descriptor_pool'],
        descriptor_set_count = descriptor_set_count,
        set_layouts = set_layouts_ptr
    )

def allocate_descriptor_sets(api, device, info):
    sets = (vk.DescriptorSet*info.descriptor_set_count)()
    result = api.AllocateDescriptorSets(device, info, array_pointer(sets))
    if result != vk.SUCCESS:
        raise RuntimeError("Failed to create descriptor sets")

    return tuple(vk.DescriptorSet(d) for d in sets)


def write_descriptor_set(**kwargs):
    required_arguments = ('dst_set', 'dst_binding', 'descriptor_type')
    check_ctypes_members(vk.WriteDescriptorSet, required_arguments, kwargs.keys())

    _images, _buffers, _texel_buffer_views = kwargs.get('image_info'), kwargs.get('buffer_info'), kwargs.get('texel_buffer_view')

    images, images_ptr, image_count = sequence_to_array(_images, vk.DescriptorImageInfo)
    buffers, buffers_ptr, buffer_count = sequence_to_array(_buffers, vk.DescriptorBufferInfo)
    texel_buffer_views, texel_buffer_views_ptr, texel_buffer_view_count = sequence_to_array(_texel_buffer_views, vk.BufferView)

    if _images is not None:
        descriptor_count = image_count
    elif _buffers is not None:
        descriptor_count = buffer_count
    elif _texel_buffer_views is not None:
        descriptor_count = texel_buffer_view_count

    return vk.WriteDescriptorSet(
        type = vk.STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
        next = None,
        dst_set = kwargs['dst_set'],
        dst_binding = kwargs['dst_binding'],
        dst_array_element = kwargs.get('dst_array_element', 0),
        descriptor_count = descriptor_count,
        descriptor_type = kwargs['descriptor_type'],
        image_info = images_ptr,
        buffer_info = buffers_ptr,
        texel_buffer_view = texel_buffer_views_ptr
    )

def update_descriptor_sets(api, device, write, copy):
    writes, writes_ptr, write_count = sequence_to_array(write, vk.WriteDescriptorSet)
    copies, copies_ptr, copy_count = sequence_to_array(copy, vk.CopyDescriptorSet)
    api.UpdateDescriptorSets(device, write_count, writes_ptr, copy_count, copies_ptr)
