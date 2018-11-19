from vulkan import vk, helpers as hvk


class DataShader(object):

    def __init__(self, engine, shader):
        self.engine = engine
        self.shader = shader

        self.modules = None
        self.stage_infos = None
        self.vertex_input_state = None
        self.pipeline_layout = None

        self._compile_shader()
        self._setup_vertex_state()
        self._setup_pipeline_layout()

    def free(self):
        engine, api, device = self.ctx
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

        self.vertex_input_state = hvk.pipeline_vertex_input_state_create_info(
            vertex_binding_descriptions = bindings,
            vertex_attribute_descriptions = attributes
        )

    def _setup_pipeline_layout(self):
        _, api, device = self.ctx

        set_layouts = []

        layout = hvk.create_pipeline_layout(api, device, hvk.pipeline_layout_create_info(
            set_layouts = set_layouts
        ))

        self.pipeline_layout = layout
