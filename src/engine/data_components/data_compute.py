from vulkan import vk, helpers as hvk
from .shared import ShaderScope, setup_descriptor_layouts, setup_specialization_constants


class DataCompute(object):

    def __init__(self, engine, compute):
        self.engine = engine
        self.compute = compute
        self.sync = True

        self.module = None
        self.module_stage = None
        self.queue = None

        self.descriptor_set_layouts = None
        self.pipeline_layout = None
        self.pipeline = None                # Set by DataScene._setup_compute_pipelines
        self.command_index = None           # Set by DataScene._setup_compute_commands

        self.descriptor_sets = None
        self.write_sets_update_infos = None
        self.write_sets = None

        self.fence = None

        self._fetch_queue()
        self._setup_sync()
        self._compile_shader()
        self._setup_descriptor_layouts()
        self._setup_pipeline_layout()

    def free(self):
        engine, api, device = self.ctx

        for dset_layout in self.descriptor_set_layouts:
            hvk.destroy_descriptor_set_layout(api, device, dset_layout.set_layout)

        hvk.destroy_pipeline_layout(api, device, self.pipeline_layout)
        hvk.destroy_shader_module(api, device, self.module)
        hvk.destroy_fence(api, device, self.fence)

        del self.engine

    @property
    def ctx(self):
        engine = self.engine
        api, device = engine.api, engine.device
        return engine, api, device

    @property
    def global_layouts(self):
        return (l for l in self.descriptor_set_layouts if l.scope is ShaderScope.GLOBAL)

    def _fetch_queue(self):
        engine = self.engine
        render_queue = engine.render_queue

        queue_name = self.compute.queue
        queue = engine.queues.get(queue_name)
        if queue is None:
            raise ValueError(f"No queue named \"{queue_name}\" in the engine")

        self.sync = render_queue.handle == queue.handle
        self.queue = queue

    def _setup_sync(self):
        _, api, device = self.ctx
        fence_info = hvk.fence_create_info()
        fence = hvk.create_fence(api, device, fence_info)
        self.fence = fence

    def _compile_shader(self):
        engine, api, device = self.ctx
        compute = self.compute

        module = hvk.create_shader_module(api, device, hvk.shader_module_create_info(code=compute.src))

        spez = None
        constants = compute.mapping.get('constants')
        if constants is not None and len(constants) > 0:
            spez = setup_specialization_constants(vk.SHADER_STAGE_COMPUTE_BIT, constants)

        stage = hvk.pipeline_shader_stage_create_info(
            stage = vk.SHADER_STAGE_COMPUTE_BIT,
            module = module,
            specialization_info = spez
        )

        self.module = module
        self.module_stage = stage

    def _setup_descriptor_layouts(self):
        engine, api, device = self.ctx
        mappings = self.compute.mapping
        self.descriptor_set_layouts = setup_descriptor_layouts(self, engine, api, device, mappings)

    def _setup_pipeline_layout(self):
        _, api, device = self.ctx

        set_layouts = self.descriptor_set_layouts or ()
        set_layouts = [l.set_layout for l in set_layouts]

        self.pipeline_layout = hvk.create_pipeline_layout(api, device, hvk.pipeline_layout_create_info(
            set_layouts = set_layouts
        ))
