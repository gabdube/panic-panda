from ctypes import Structure, sizeof, c_uint8, c_int32, c_float
from vulkan import vk, helpers as hvk
from functools import lru_cache
from enum import Enum
from io import BytesIO


class DescriptorSetLayout(object):

    def __init__(self, set_layout, scope, index, struct_map, images, pool_size_counts, write_set_templates):
        self.set_layout = set_layout
        self.index = index
        self.scope = ShaderScope(scope)
        self.struct_map = struct_map
        self.images = images
        self.pool_size_counts = pool_size_counts
        self.write_set_templates = write_set_templates

        self.struct_map_size_bytes = sum( sizeof(s) for s in struct_map.values() )


class UniformMemberType(Enum):
    FLOAT_MAT2 = 0
    FLOAT_MAT3 = 1
    FLOAT_MAT4 = 2

    FLOAT_VEC2 = 3
    FLOAT_VEC3 = 4
    FLOAT_VEC4 = 5

    INT_MAT2 = 6
    INT_MAT3 = 7
    INT_MAT4 = 8

    INT_VEC2 = 9
    INT_VEC3 = 10
    INT_VEC4 = 11

    FLOAT = 12
    INT = 13
    BOOL = 14


class ShaderScope(Enum):
    # Allocate a descriptor set per shader
    GLOBAL = 0

    # Allocate a descriptor set per object linked to a shader
    LOCAL = 1

    # Allocate a descriptor set per object linked to the shader
    # Data is managed by the engine
    ENGINE_ANIMATION = 2


class BufferRange(object):
    """
        Keep in memory what range of a buffer has been allocated to some resources and
        what other parts are still free to use
    """

    __slots__ = ('allocated', 'free', 'total_size')

    def __init__(self, inital_size):
        self.total_size = inital_size
        self.free = [(0, inital_size)]
        self.allocated = []

    def allocate(self, alloc_size):
        if len(self.free) == 0:
            raise ValueError("No free space left in buffer")
        elif alloc_size > self.total_size:
            raise ValueError(f"Tried to allocate more that the total buffer size. Total: {self.total_size}, Allocated: {alloc_size}")

        found = None
        for i, (i_min, i_max) in enumerate(self.free):
            i_size = i_max - i_min
            if i_size >= alloc_size:
                found = i, i_min, i_max

        if found is None:
            raise ValueError(f"No free space left in buffer to accomodate an allocation size of {alloc_size}")

        index, min_offset, max_offset = found
        
        self.allocated.append((min_offset, alloc_size))

        if (min_offset+alloc_size) < max_offset:
            self.free[index] = (min_offset+alloc_size, max_offset)
        else:
            del self.free[index]

    def next_offset(self, min_size=None):
        if len(self.free) == 0:
            raise ValueError("No free space left in buffer")

        off = None
        for i_min, i_max in self.free:
            if min_size is None:
                off = i_min
                break
            elif (i_max-i_min) >= min_size:
                off = i_min
                break

        if off is None and min_size is not None:
            raise ValueError(f"No free space left in buffer to accomodate an allocation size of {min_size}")

        return off

def setup_descriptor_layouts(shader, engine, api, device, mappings):

    if len(mappings["uniforms"]) == 0:
            return
        
    # Uniform buffers offsets MUST absolutly be aligned to minUniformBufferOffsetAlignment 
    # On AMD: 16 bytes
    # On INTEL: 32 bytes
    # On NVDIA, 256 bits
    limits = engine.info["limits"]
    uniform_buffer_align = limits.min_uniform_buffer_offset_alignment 

    layouts = []

    def init_fn(me, **defaults):
        me_cls = type(me)
        members = [name for name, _ in me_cls._fields_]
        bad_members = [m for m in defaults.keys() if not m in members]
        if len(bad_members) > 0:
            print(f"WARNING: some unkown members were found when creating uniform \"{me_cls.__qualname__}\": {bad_members}")

        super(me_cls, me).__init__(**defaults)

    def repr_fn(me):
        type_name = type(me).__qualname__
        fields = {}
        for name, ctype in me._fields_:
            value = getattr(me, name)
            if hasattr(value, '_length_'):
                fields[name] = value[::]
            else:
                fields[name] = value
                
        return f"Uniform(name={type_name}, fields={repr(fields)})"

    for dset, uniforms in group_uniforms_by_sets(mappings):
        counts, structs, images, bindings, wst = {}, {}, [], [], []

        for uniform in uniforms:
            uniform_name, dtype, dcount, ubinding = uniform["name"], uniform["type"], uniform["count"], uniform["binding"]
            buffer = True

            # Counts used for the descriptor pool max capacity
            if dtype in counts:
                counts[dtype] += dcount
            else:
                counts[dtype] = dcount

            # ctypes Struct used when allocating uniforms buffers
            struct_size = None
            if dtype in (vk.DESCRIPTOR_TYPE_UNIFORM_BUFFER, vk.DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC):
                size_of = 0
                args = []
                for field in uniform["fields"]:
                    field_name = field["name"]
                    field_ctype = uniform_member_as_ctype(field["type"], field["count"])
                    size_of += sizeof(field_ctype)
                    args.append((field_name, field_ctype))

                padding = (-size_of & (uniform_buffer_align - 1))
                if padding > 0:
                    args.append(("PADDING", c_uint8*padding))

                struct = type(uniform_name, (Structure,), {'_pack_': uniform_buffer_align, '_fields_': args,  '__init__': init_fn, '__repr__': repr_fn})
                struct_size = sizeof(struct)
                structs[uniform_name] = struct
            elif dtype in (vk.DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, vk.DESCRIPTOR_TYPE_STORAGE_IMAGE):
                images.append(uniform_name)
                buffer = False
            else:
                raise NotImplementedError(f"Descriptor type {dtype} not implemented")
            
            # Bindings for raw set layout creation
            binding = hvk.descriptor_set_layout_binding(
                binding = ubinding,
                descriptor_type = dtype,
                descriptor_count = dcount,
                stage_flags = uniform["stage"]
            )

            bindings.append(binding)

            # Write set template. Used during descriptor set creation
            wst.append({
                "name": uniform_name,
                "descriptor_type": dtype,
                "range": struct_size,
                "binding": ubinding,
                "buffer": buffer
            })

        # Associate the values to the descriptor set layout wrapper
        info = hvk.descriptor_set_layout_create_info(bindings = bindings)
        dset_layout = DescriptorSetLayout(
            set_layout = hvk.create_descriptor_set_layout(api, device, info),
            scope = dset["scope"],
            index = dset["id"],
            struct_map = structs,
            images = images,
            pool_size_counts = tuple(counts.items()),
            write_set_templates = wst,
        )

        layouts.append(dset_layout)
    
    return layouts


def group_uniforms_by_sets(mappings):
    sets = mappings["sets"]
    uniforms = mappings["uniforms"]
    
    uniforms_by_dset = {}
    for uniform in uniforms:
        dset = uniform["set"]
        if dset in uniforms_by_dset:
            uniforms_by_dset[dset].append(uniform)
        else:
            uniforms_by_dset[dset] = [uniform]

    sets_uniforms = []
    for set_id, uniforms in uniforms_by_dset.items():
        dset = next( s for s in sets if s["id"] == set_id )
        sets_uniforms.append((dset, uniforms))

    return sets_uniforms


def setup_specialization_constants(stage, contants):
    data = BytesIO()
    offset = 0
    entries = []

    filtered_constants = (c for c in contants if c['stage'] == stage)
    
    for c in filtered_constants:
        cdata = uniform_member_as_ctype(c["type"], 1)
        size = sizeof(cdata)

        default = c.get('default_value')
        if default is not None:
            data.write(cdata(default))
        else:
            data.write(cdata())

        entries.append(vk.SpecializationMapEntry(
            constant_ID = c["id"],
            offset = offset,
            size = size
        ))

        offset += size

    return hvk.specialization_info(map_entries=entries, data=data.getbuffer()) 


@lru_cache(maxsize=16)
def uniform_member_as_ctype(value, count1):
    mt = UniformMemberType
    value = mt(value)
    t = count2 = None

    if value in (mt.FLOAT_MAT2, mt.FLOAT_MAT3, mt.FLOAT_MAT4, mt.FLOAT_VEC4, mt.FLOAT_VEC2, mt.FLOAT_VEC3, mt.FLOAT):
        t = c_float
    elif value in (mt.INT_MAT2, mt.INT_MAT3, mt.INT_MAT4, mt.INT_VEC4, mt.INT_VEC2, mt.INT_VEC3, mt.INT, mt.BOOL):
        t = c_int32
    else:
        raise ValueError("Invalid uniform member type")

    if value in (mt.FLOAT_MAT2 , mt.INT_MAT2, mt.FLOAT_VEC4, mt.INT_VEC4): count2 = 4
    elif value in (mt.FLOAT_MAT3, mt.INT_MAT3): count2 = 9
    elif value in (mt.FLOAT_MAT4, mt.INT_MAT4): count2 = 16
    elif value in (mt.FLOAT_VEC2, mt.INT_VEC2): count2 = 2
    elif value in (mt.FLOAT_VEC3, mt.INT_VEC3): count2 = 3
    elif value in (mt.FLOAT, mt.INT, mt.BOOL): count2 = 1
    else:
        raise ValueError("Invalid uniform member type")
    
    return t*(count1*count2)

