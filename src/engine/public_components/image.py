from ..base_types import name_generator
from vulkan import vk, helpers as hvk
from collections import namedtuple
from enum import Enum


MipmapData = namedtuple('MipmapData', ('level', 'offset', 'size', 'width', 'height'))
CombinedImageSampler = namedtuple("CombinedImageSampler", ("image_id", "view_name", "sampler_id"))
image_name = name_generator("Image")


class ImageSource(Enum):
    Ktx = 0


class ImageView(object):

    def __init__(self, **kw):
        self.params = dict(
            view_type = kw.get('view_type', vk.IMAGE_VIEW_TYPE_2D),
            format = kw['format'],
            components = kw.get('components', hvk.component_mapping()),
            subresource_range = kw.get('subresource_range', hvk.image_subresource_range())
        )
    
    @classmethod
    def from_params(cls, **params):
        view = super().__new__(cls)
        view.__init__(**params)
        return view


class Image(object):

    def __init__(self, **kwargs):
        self.id = None
        self.name = kwargs.get('name', next(image_name))
        
        self.views = {}

        self.source_type = None
        self.source = None

        self.format = None
        self.extent = None
        self.mipmaps_levels = None
        self.texture_size = None

    @classmethod
    def from_ktx(cls, ktx_file, **kwargs):
        f = ktx_file

        image = super().__new__(cls)
        image.__init__(**kwargs)

        image.source_type = ImageSource.Ktx
        image.source = f

        image.format = f.format
        image.extent = (f.width, f.height, f.depth)
        image.mipmaps_levels = f.mips_level
        image.texture_size = len(f.data)

        if kwargs.get("nodefault", False) != True:
            subs_range = hvk.image_subresource_range(level_count = f.mips_level)
            image.views["default"] = ImageView.from_params(
                view_type=f.target,
                format=f.format,
                subresource_range=subs_range
            )

        return image

    def mipmaps(self):
        src, src_t = self.source, self.source_type
        if src_t is ImageSource.Ktx:
            for mipmap in src.mipmaps:
                yield MipmapData(mipmap.level, mipmap.offset, mipmap.size, mipmap.width, mipmap.height)

    def size(self):
        return self.texture_size


