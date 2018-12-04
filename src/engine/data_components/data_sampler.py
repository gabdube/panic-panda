from vulkan import vk, helpers as hvk


class DataSampler(object):

    def __init__(self, engine, sampler):
        self.engine = engine
        self.sampler = sampler

        self.sampler_handle = None

        self._setup_sampler()

    def free(self):
        engine, api, device = self.ctx
        hvk.destroy_sampler(api, device, self.sampler_handle)

    @property
    def ctx(self):
        engine = self.engine
        api, device = engine.api, engine.device
        return engine, api, device

    def _setup_sampler(self):
        engine, api, device = self.ctx
        self.sampler_handle = hvk.create_sampler(api, device, hvk.sampler_create_info(**self.sampler.params))
