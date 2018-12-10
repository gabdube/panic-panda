from ..public_components import ImageSource
from vulkan import vk, helpers as hvk
from ctypes import c_ubyte


class DataImage(object):
    
    def __init__(self, engine, image, base_staging_offset):
        self.engine = engine
        self.image = image

        self.base_staging_offset = base_staging_offset
        self.base_offset = 0                            # Set in `DataScene._setup_images_resources`

        self.image_handle = None
        self.layout = None
        self.views = {}

        self._setup_image()

    def free(self):
        engine, api, device = self.ctx

        hvk.destroy_image(api, device, self.image_handle)

    @property
    def ctx(self):
        engine = self.engine
        api, device = engine.api, engine.device
        return engine, api, device

    def as_ctypes_array(self):
        img = self.image
        data = hvk.array(c_ubyte, img.texture_size, img.texture_data())
        return data

    def _setup_image(self):
        engine, api, device = self.ctx

        img = self.image
        width, height, depth = img.extent

        image = hvk.create_image(api, device, hvk.image_create_info(
            flags = img.flags,
            format = img.format,
            mip_levels = img.mipmaps_levels,
            array_layers = img.array_layers,
            extent = vk.Extent3D(width, height, depth),
            usage = vk.IMAGE_USAGE_TRANSFER_DST_BIT | vk.IMAGE_USAGE_SAMPLED_BIT
        ))

        self.image_handle = image
        self.layout = vk.IMAGE_LAYOUT_UNDEFINED

    def _setup_views(self):
        # Called from `DataScene._setup_images_resources` after the memory is bound to the image
        _, api, device = self.ctx
        image_handle = self.image_handle
        for name, view_info in self.image.views.items():
            view_create_info = hvk.image_view_create_info(image=image_handle, **view_info.params)
            view = hvk.create_image_view(api, device, view_create_info)
            self.views[name] = view
