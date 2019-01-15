from vulkan import vk, helpers as hvk


class ComputeRunner(object):

    def __init__(self, engine):
        self.engine = engine
        self.running = set()

    def free(self):
        del self.engine

    @property
    def ctx(self):
        engine = self.engine
        api, device = engine.api, engine.device
        return engine, api, device

    def run(self, data_scene, data_compute, group, sync, after, before, callback):
        if data_compute in self.running:
            raise RuntimeError(f"Compute shader {data_compute.compute.name} is already running")

        engine, api, device = self.ctx
        cmd = data_scene.compute_commands[data_compute.command_index]
        pipeline = data_scene.compute_pipelines[data_compute.pipeline]
        x, y, z = group
        
        hvk.begin_command_buffer(api, cmd, hvk.command_buffer_begin_info())

        hvk.bind_pipeline(api, cmd, pipeline, vk.PIPELINE_BIND_POINT_COMPUTE)
        hvk.bind_descriptor_sets(api, cmd, vk.PIPELINE_BIND_POINT_COMPUTE, data_compute.pipeline_layout, data_compute.descriptor_sets)

        if before is not None:
            before()

        hvk.dispatch(api, cmd, x, y, z)
        
        if after is not None:
            after()

        hvk.end_command_buffer(api, cmd)

        self.running.add(data_compute)
