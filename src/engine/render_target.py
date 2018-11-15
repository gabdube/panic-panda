from vulkan import vk, helpers as hvk
from . import ImageAndView


class RenderTarget(object):

    def __init__(self, engine):
        self.engine = engine
        self.depth_stencil = None
        self.depth_stencil_alloc = None
        self.render_pass = None
        self.framebuffers = None
        self.swapchain_images = []

        self._setup_swapchain_images()
        self._setup_depth_stencil()
        self._setup_render_pass()
        self._setup_framebuffers()

    def free(self):
        ctx, api, device = self.ctx
        memory_manager = ctx.memory_manager

        hvk.destroy_image_view(api, device, self.depth_stencil.view)
        hvk.destroy_image(api, device, self.depth_stencil.image)
        memory_manager.free_alloc(self.depth_stencil_alloc)

        for fb in self.framebuffers:
            hvk.destroy_framebuffer(api, device, fb)
        
        for (_, view) in self.swapchain_images:
            hvk.destroy_image_view(api, device, view)

        hvk.destroy_render_pass(api, device, self.render_pass)
        del self.engine

    @property
    def framebuffer_count(self):
        return len(self.framebuffers)

    @property
    def ctx(self):
        engine = self.engine
        api, device = engine.api, engine.device
        return engine, api, device

    def _setup_swapchain_images(self):
        engine, api, device = self.ctx
        swapchain = engine.swapchain

        # Fetch swapchain images
        swapchain_images = hvk.swapchain_images(api, device, swapchain)
        swapchain_fmt = engine.info["swapchain_format"]

        # Create the swapchain images view
        self.swapchain_images = []
        for image in swapchain_images:
            view = hvk.create_image_view(api, device, hvk.image_view_create_info(
                image = image,
                format = swapchain_fmt
            ))

            self.swapchain_images.append(ImageAndView(image=image, view=view))

    def _setup_depth_stencil(self):
        ctx, api, device = self.ctx
        width, height = ctx.info["swapchain_extent"].values()
        depth_format = ctx.info["depth_format"]

        depth_stencil_image = hvk.create_image(api, device, hvk.image_create_info(
            format = depth_format,
            extent = vk.Extent3D(width=width, height=height, depth=1),
            usage = vk.IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT
        ))

        alloc = ctx.memory_manager.alloc(depth_stencil_image, vk.STRUCTURE_TYPE_IMAGE_CREATE_INFO,
            types = (vk.MEMORY_PROPERTY_DEVICE_LOCAL_BIT,)
        )

        depth_stencil_view = hvk.create_image_view(api, device, hvk.image_view_create_info(
            image = depth_stencil_image,
            format = depth_format,
            subresource_range = hvk.image_subresource_range(aspect_mask=vk.IMAGE_ASPECT_DEPTH_BIT|vk.IMAGE_ASPECT_STENCIL_BIT)
        ))

        self.depth_stencil = ImageAndView(image=depth_stencil_image, view=depth_stencil_view)
        self.depth_stencil_alloc = alloc

    def _setup_render_pass(self):
        ctx, api, device = self.ctx
        image_format = ctx.info["swapchain_format"]
        depth_format = ctx.info["depth_format"]

        color = hvk.attachment_description(
            format = image_format,
            initial_layout = vk.IMAGE_LAYOUT_UNDEFINED,
            final_layout = vk.IMAGE_LAYOUT_PRESENT_SRC_KHR
        )

        depth = hvk.attachment_description(
            format = depth_format,
            initial_layout = vk.IMAGE_LAYOUT_UNDEFINED,
            final_layout = vk.IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL
        )

        # Render pass subpasses
        color_ref = vk.AttachmentReference(attachment=0, layout=vk.IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL)
        depth_ref = vk.AttachmentReference(attachment=1, layout=vk.IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL)
        subpass_info = hvk.subpass_description(
            pipeline_bind_point = vk.PIPELINE_BIND_POINT_GRAPHICS,
            color_attachments = (color_ref,),
            depth_stencil_attachment = depth_ref
        )

        # Renderpass dependencies
        prepare_drawing = hvk.subpass_dependency(
            src_subpass = vk.SUBPASS_EXTERNAL,
            dst_subpass = 0,
            src_stage_mask = vk.PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,
            dst_stage_mask = vk.PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
            src_access_mask = vk.ACCESS_MEMORY_READ_BIT,
            dst_access_mask = vk.ACCESS_COLOR_ATTACHMENT_READ_BIT | vk.ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
        )

        prepare_present = hvk.subpass_dependency(
            src_subpass = 0,
            dst_subpass = vk.SUBPASS_EXTERNAL,
            src_stage_mask = vk.PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
            dst_stage_mask = vk.PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT,
            src_access_mask = vk.ACCESS_COLOR_ATTACHMENT_READ_BIT | vk.ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
            dst_access_mask = vk.ACCESS_MEMORY_READ_BIT,
        )

        # Render pass creation
        self.render_pass = hvk.create_render_pass(api, device, hvk.render_pass_create_info(
            attachments = (color, depth),
            subpasses = (subpass_info,),
            dependencies = (prepare_drawing, prepare_present)
        ))

    def _setup_framebuffers(self):
        ctx, api, device = self.ctx
        render_pass = self.render_pass
        width, height = ctx.info["swapchain_extent"].values()

        depth_view = self.depth_stencil.view
        framebuffers = []

        for _, color_view in self.swapchain_images:
            framebuffer = hvk.create_framebuffer(api, device, hvk.framebuffer_create_info(
                render_pass = render_pass,
                width = width,
                height = height,
                attachments = (color_view, depth_view)
            ))

            framebuffers.append(framebuffer)

        self.framebuffers = framebuffers
