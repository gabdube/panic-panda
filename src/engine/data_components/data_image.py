from ctypes import c_ubyte
from vulkan import vk, helpers as hvk
from ..public_components import ImageSource


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
        if img.source_type is ImageSource.Ktx:
            src = img.source
            return hvk.array(c_ubyte, len(src.data), src.data)
        else:
            raise NotImplementedError(f"Method `as_ctypes_array` is not implemented for images of type {img.source_type}")

    def _setup_image(self):
        engine, api, device = self.ctx

        img = self.image
        width, height, depth = img.extent

        image = hvk.create_image(api, device, hvk.image_create_info(
            format = img.format,
            mip_levels = img.mipmaps_levels,
            extent = vk.Extent3D(width, height, depth),
            usage = vk.IMAGE_USAGE_TRANSFER_DST_BIT | vk.IMAGE_USAGE_SAMPLED_BIT,
        ))

        self.image_handle = image
        self.layout = vk.IMAGE_LAYOUT_UNDEFINED
