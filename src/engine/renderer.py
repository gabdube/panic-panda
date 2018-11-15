from vulkan import vk, helpers as hvk


class Renderer(object):

    def __init__(self, engine):
        self.engine = engine

        self.image_ready = None
        self.rendering_done = None
        self.render_fences = ()
        self.render_cache = {}

        self._setup_sync()
        self._setup_render_cache()

    def free(self):
        engine, api, device = self.ctx
        hvk.destroy_semaphore(api, device, self.image_ready)
        hvk.destroy_semaphore(api, device, self.rendering_done)

        for f in self.render_fences:
            hvk.destroy_fence(api, device, f)

        del self.engine

    @property
    def ctx(self):
        engine = self.engine
        api, device = engine.api, engine.device
        return engine, api, device

    def render(self, scene_data):
        engine, api, device = self.ctx
        swapchain = engine.swapchain
        render_queue = engine.render_queue
        rc = self.render_cache

        image_index, result = hvk.acquire_next_image(api, device, swapchain, semaphore = self.image_ready)

        fence = self.render_fences[image_index]
        hvk.wait_for_fences(api, device, (fence,))
        hvk.reset_fences(api, device, (fence,))

        scene_data.record(image_index)

        submit = rc["submit_info"]
        submit.command_buffers[0] = scene_data.render_commands[image_index]
        hvk.queue_submit(api, render_queue.handle, (submit,), fence = fence)

        present = rc["present_info"]
        present.image_indices[0] = image_index
        hvk.queue_present(api, render_queue.handle, present)

    def _setup_sync(self):
        engine, api, device = self.ctx
        info = hvk.semaphore_create_info()
        
        self.image_ready = hvk.create_semaphore(api, device, info)
        self.rendering_done = hvk.create_semaphore(api, device, info)

        self.render_fences = []
        info = hvk.fence_create_info(flags=vk.FENCE_CREATE_SIGNALED_BIT)
        for _ in range(len(engine.render_target.swapchain_images)):
            self.render_fences.append(hvk.create_fence(api, device, info))

    def _setup_render_cache(self):
        engine = self.engine

        self.render_cache["submit_info"] = hvk.submit_info(
            wait_dst_stage_mask = (vk.PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,),
            wait_semaphores = (self.image_ready,),
            signal_semaphores = (self.rendering_done,),
            command_buffers = (0,)
        )

        self.render_cache["present_info"] = hvk.present_info(
            swapchains = (engine.swapchain,),
            image_indices = (0,),
            wait_semaphores = (self.rendering_done,)
        )
    