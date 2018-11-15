from vulkan import vk, helpers as hvk


class DataShader(object):

    def __init__(self, engine, shader):
        self.engine = engine
        self.shader = shader

        self.modules = None
        self.stage_infos = None

        self._compile_shader()

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
