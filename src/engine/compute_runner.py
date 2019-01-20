from vulkan import vk, helpers as hvk
from .data_components.commands_runner import CommandsRunner


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
        queue = data_compute.queue
        cmd = data_scene.compute_commands[data_compute.command_index]
        pipeline = data_scene.compute_pipelines[data_compute.pipeline]
        x, y, z = group

        before = () if before is None else before
        after = () if after is None else after
        
        # Record the commands
        hvk.begin_command_buffer(api, cmd, hvk.command_buffer_begin_info())

        hvk.bind_pipeline(api, cmd, pipeline, vk.PIPELINE_BIND_POINT_COMPUTE)
        hvk.bind_descriptor_sets(api, cmd, vk.PIPELINE_BIND_POINT_COMPUTE, data_compute.pipeline_layout, data_compute.descriptor_sets)

        CommandsRunner.run_device(before, api, cmd, queue, data_scene)
        hvk.dispatch(api, cmd, x, y, z)
        CommandsRunner.run_device(after, api, cmd, queue, data_scene)

        hvk.end_command_buffer(api, cmd)    

        # Execute the command buffer 
        cmds = (cmd,)
        fence = data_compute.fence
        infos = (hvk.submit_info(command_buffers=cmds),)
        hvk.queue_submit(api, queue.handle, infos, fence)

        if sync:
            f = (fence,)
            hvk.wait_for_fences(api, device, f)
            hvk.reset_fences(api, device, f)
    
            CommandsRunner.run_app(before, data_scene)
            CommandsRunner.run_app(after, data_scene)
            callback()
        else:
            self.running.add(data_compute)
            raise NotImplementedError("Compute without sync is not yet implemented")
