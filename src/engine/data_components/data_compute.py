from vulkan import helpers as hvk
from .shared import setup_descriptor_layouts

class DataCompute(object):

    def __init__(self, engine, compute):
        self.engine = engine
        self.compute = compute
        self.sync = True

        self.module = None
        self.queue = None

        self.descriptor_set_layouts = None
        self.pipeline_layout = None

        self._fetch_queue()
        self._compile_shader()
        self._setup_descriptor_layouts()

    def free(self):
        engine, api, device = self.ctx

        for dset_layout in self.descriptor_set_layouts:
            hvk.destroy_descriptor_set_layout(api, device, dset_layout.set_layout)

        hvk.destroy_shader_module(api, device, self.module)

        del self.engine

    @property
    def ctx(self):
        engine = self.engine
        api, device = engine.api, engine.device
        return engine, api, device

    def _fetch_queue(self):
        engine = self.engine
        render_queue = engine.render_queue

        queue_name = self.compute.queue
        queue = engine.queues.get(queue_name)
        if queue is None:
            raise ValueError(f"No queue named \"{queue_name}\" in the engine")

        self.sync = render_queue.handle == queue.handle
        self.queue = queue

    def _compile_shader(self):
        engine, api, device = self.ctx
        compute = self.compute

        module = hvk.create_shader_module(api, device, hvk.shader_module_create_info(code=compute.src))

        self.module = module

    def _setup_descriptor_layouts(self):
        engine, api, device = self.ctx
        mappings = self.compute.mapping
        self.descriptor_set_layouts = setup_descriptor_layouts(self, engine, api, device, mappings)
