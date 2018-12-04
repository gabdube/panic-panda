from ..base_types import name_generator
from vulkan import vk


sampler_name = name_generator("Sampler")


class Sampler(object):

    def __init__(self, **kw):
        self.id = None
        self.name = kw.get('name', next(sampler_name))

        self.params = dict(
            mag_filter = kw.get('mag_filter', vk.FILTER_LINEAR),
            min_filter = kw.get('min_filter', vk.FILTER_LINEAR),
            mipmap_mode = kw.get('mipmap_mode', vk.SAMPLER_MIPMAP_MODE_LINEAR),
            address_mode_V = kw.get('address_mode_V', vk.SAMPLER_ADDRESS_MODE_REPEAT),
            address_mode_U = kw.get('address_mode_U', vk.SAMPLER_ADDRESS_MODE_REPEAT),
            address_mode_W = kw.get('address_mode_W', vk.SAMPLER_ADDRESS_MODE_REPEAT),
            mip_lod_bias = kw.get('mip_lod_bias', 0.0),
            anisotropy_enable = kw.get('anisotropy_enable', vk.FALSE),
            max_anisotropy = kw.get('max_anisotropy', 1.0),
            compare_enable = kw.get('compare_enable', vk.FALSE),
            compare_op = kw.get('compare_op', vk.COMPARE_OP_NEVER),
            min_lod = kw.get('min_lod', 0.0),
            max_lod = kw.get('max_lod', 0.0),
            border_color = kw.get('border_color', vk.BORDER_COLOR_FLOAT_TRANSPARENT_BLACK),
            unnormalized_coordinates = kw.get('unnormalized_coordinates', vk.FALSE)
        )

    @classmethod
    def from_params(cls, **params):
        sampler = super().__new__(cls)
        sampler.__init__(**params)
        return sampler
