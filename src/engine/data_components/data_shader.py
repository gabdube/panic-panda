from vulkan import vk, helpers as hvk
from ctypes import Structure, c_float
from functools import lru_cache
from enum import Enum


class DataShader(object):

    def __init__(self, engine, shader):
        self.engine = engine
        self.shader = shader

        self.modules = None
        self.stage_infos = None

        self.vertex_input_state = None
        self.ordered_attribute_names = None

        self.descriptor_set_layout = None
        self.descriptor_set_structs = None
        self.pipeline_layout = None

        self._compile_shader()
        self._setup_vertex_state()
        self._setup_descriptor_layouts()
        self._setup_pipeline_layout()

    def free(self):
        engine, api, device = self.ctx

        hvk.destroy_descriptor_set_layout(api, device, self.descriptor_set_layout)

        hvk.destroy_pipeline_layout(api, device, self.pipeline_layout)

        for m in self.modules:
            hvk.destroy_shader_module(api, device, m)

        del self.engine

    @property
    def ctx(self):
        engine = self.engine
        api, device = engine.api, engine.device
        return engine, api, device

    def _compile_shader(self):
        engine, api, device = self.ctx
        shader = self.shader
        modules = []
        stage_infos = []

        modules_src = (
            (vk.SHADER_STAGE_VERTEX_BIT, shader.vert),
            (vk.SHADER_STAGE_FRAGMENT_BIT, shader.frag),
        )

        for stage, code in modules_src:
            module = hvk.create_shader_module(api, device, hvk.shader_module_create_info(code=code))
            modules.append(module)

            stage_infos.append(hvk.pipeline_shader_stage_create_info(
                stage = stage,
                module = module,
            ))

        self.modules = modules
        self.stage_infos = stage_infos

    def _setup_vertex_state(self):
        mapping = self.shader.mapping
        bindings = []
        attributes = []
        attribute_names = []
        
        for binding in mapping["bindings"]:
            bindings.append(hvk.vertex_input_binding_description(
                binding = binding["id"],
                stride = binding["stride"]
            ))

        for attr in mapping["attributes"]:
            attributes.append(hvk.vertex_input_attribute_description(
                location = attr["location"],
                binding = attr["binding"],
                format = attr["format"],
                offset = attr.get("offset", 0)
            ))

        self.ordered_attribute_names = tuple(a["name"] for a in sorted(mapping["attributes"], key = lambda i: i["binding"]))

        self.vertex_input_state = hvk.pipeline_vertex_input_state_create_info(
            vertex_binding_descriptions = bindings,
            vertex_attribute_descriptions = attributes
        )

    def _setup_descriptor_layouts(self):
        _, api, device = self.ctx
        uniforms = self.shader.mapping["uniforms"]
        bindings = []
        structs = {}

        repr_fn = lambda self: f"Uniform(name={self.__qualname__}, fields={str(dict(self._fields_))})"
        
        for uniform in uniforms:
            uniform_name = uniform["name"]
            
            args = []
            for field in uniform["fields"]:
                field_name = field["name"]
                field_ctype = uniform_member_as_ctype(field["type"], field["count"])
                args.append((field_name, field_ctype))

            struct = type(uniform_name, (Structure,), {'_fields_': args, '__repr__': repr_fn})
            
            binding = hvk.descriptor_set_layout_binding(
                binding = uniform["binding"],
                descriptor_type = uniform["type"],
                descriptor_count = uniform["count"],
                stage_flags = uniform["stage"]
            )

            structs[uniform_name] = struct
            bindings.append(binding)

        info = hvk.descriptor_set_layout_create_info(bindings = bindings)
        self.descriptor_set_layout = hvk.create_descriptor_set_layout(api, device, info)
        self.descriptor_set_structs = structs

    def _setup_pipeline_layout(self):
        _, api, device = self.ctx

        self.pipeline_layout = hvk.create_pipeline_layout(api, device, hvk.pipeline_layout_create_info(
            set_layouts = (self.descriptor_set_layout,)
        ))


class UniformMemberType(Enum):
    FLOAT_MAT2 = 0
    FLOAT_MAT3 = 1
    FLOAT_MAT4 = 2


@lru_cache(maxsize=16)
def uniform_member_as_ctype(value, count1):
    mt = UniformMemberType
    value = mt(value)
    t = count2 = None

    if value is mt.FLOAT_MAT2:
        t = c_float 
        count2 = 4
    elif value is mt.FLOAT_MAT3:
        t = c_float 
        count2 = 9
    elif value is mt.FLOAT_MAT4:
        t = c_float 
        count2 = 16
    else:
        raise ValueError("Invalid uniform member type")
    
    return t*(count1*count2)
