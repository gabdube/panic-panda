from ..base_types import name_generator, Id
from ..assets import KTXFile, EnvCubemapFile, IMAGE_PATH
from vulkan import vk, helpers as hvk
from collections import namedtuple
from enum import Enum
from pathlib import Path


MipmapData = namedtuple('MipmapData', ('level', 'layer', 'offset', 'size', 'width', 'height'))
CombinedImageSampler = namedtuple("CombinedImageSampler", ("image_id", "view_name", "sampler_id"))
image_name = name_generator("Image")

IMAGE_FORMAT_PIXEL_SIZE = {
    vk.FORMAT_R32_SFLOAT: 4,
    vk.FORMAT_R32G32B32_SFLOAT: 12
}


class ImageSource(Enum):
    Ktx = 0
    Uncompressed = 1
    EnvCubemap = 2


class ImageCubemapFaces(Enum):
    Right = 0
    Left = 1
    Top = 2
    Bottom = 3
    Front = 4
    Back = 5


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
    """
        A user interface over an image.
        Images must be created with the appropriate constructor (ex: `from_ktx`) and not using the constructor

        Image are subscriptable if the underlying source file is too. Each index in the image correspond to a mipmap level.
        Indexing or slicing an image copy the data and returns another Image that can be used just like the original.
    """

    def __init__(self, **kwargs):
        self._id = Id()
        self.name = kwargs.get('name', next(image_name))
        
        self.views = {}

        self.source_type = None
        self.source = None

        self.flags = 0
        self.format = None
        self.extent = None
        self.mipmaps_levels = None
        self.array_layers = 1
        self.texture_size = None

    @classmethod
    def empty(cls, **kwargs):
        keys = tuple(kwargs.keys())
        if ("format" not in keys) or ("extent" not in keys):
            raise ValueError("Image `format` and `extent` must be specified as keyword arguments")
        if kwargs.get("no_default_view", False) == False and ("default_view_type" not in keys):
            raise ValueError("If a default image view is generated, `default_view_type` must be specified as a keyword argument")

        size_bytes = Image._uncompressed_image_size(kwargs["extent"], kwargs["format"])
        data = bytes(size_bytes)
        return cls.from_uncompressed(data, **kwargs)

    @classmethod
    def from_ktx(cls, ktx_file, **kwargs):
        f = ktx_file
        if not isinstance(f, KTXFile):
            raise RuntimeError(f"File must be KTXFile, got {type(f).__qualname__}")

        image = super().__new__(cls)
        image.__init__(**kwargs)

        image.source_type = ImageSource.Ktx
        image.source = f

        image.flags = f.vk_flags
        image.format = f.vk_format
        image.extent = (f.width, f.height, f.depth)
        image.mipmaps_levels = f.mips_level
        image.texture_size = f.texture_size
        image.array_layers = f.faces * f.array_element

        if kwargs.get("no_default_view", False) != True:
            subs_range = hvk.image_subresource_range(level_count = f.mips_level, layer_count=image.array_layers)
            image.views["default"] = ImageView.from_params(
                view_type=f.vk_view_type,
                format=f.vk_format,
                subresource_range=subs_range
            )

        return image

    @classmethod
    def from_env_cubemap(cls, env_file, **kwargs):
        f = env_file
        if not isinstance(f, EnvCubemapFile):
            raise RuntimeError(f"File must be EnvCubemapFile, got {type(f).__qualname__}")

        image = super().__new__(cls)
        image.__init__(**kwargs)

        image.source_type = ImageSource.EnvCubemap
        image.source = f

        image.flags = vk.IMAGE_CREATE_CUBE_COMPATIBLE_BIT
        image.format = vk.FORMAT_R8G8B8A8_UNORM
        image.extent = (f.width, f.height, 1)
        image.mipmaps_levels = f.mips_level
        image.texture_size = f.texture_size
        image.array_layers = 6

        if kwargs.get("no_default_view", False) != True:
            subs_range = hvk.image_subresource_range(level_count = f.mips_level, layer_count = 6)
            image.views["default"] = ImageView.from_params(
                view_type=vk.IMAGE_VIEW_TYPE_CUBE,
                format=vk.FORMAT_R8G8B8A8_UNORM,
                subresource_range=subs_range
            )

        return image

    @classmethod
    def from_uncompressed(cls, data, **kwargs):
        keys = tuple(kwargs.keys())
        if ("format" not in keys) or ("extent" not in keys):
            raise ValueError("Image `format` and `extent` must be specified as keyword arguments")
        if kwargs.get("no_default_view", False) == False and ("default_view_type" not in keys):
            raise ValueError("If a default image view is generated, `default_view_type` must be specified as a keyword argument")

        image = super().__new__(cls)
        image.__init__(**kwargs)

        image.source_type = ImageSource.Uncompressed
        image.source = data

        image.flags = kwargs.get('flags', 0)
        image.format = kwargs["format"]
        image.extent = kwargs["extent"]
        image.mipmaps_levels = 1
        image.texture_size = len(data)
        image.array_layers = 1

        if kwargs.get("no_default_view", False) != True:
            subs_range = hvk.image_subresource_range(level_count = image.mipmaps_levels, layer_count = image.array_layers)
            image.views["default"] = ImageView.from_params(
                view_type=kwargs["default_view_type"],
                format=image.format,
                subresource_range=subs_range
            )

        return image

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id.value = value

    def texture_data(self):
        src, st = self.source, self.source_type
        if st is ImageSource.Ktx:
            data = bytearray(self.texture_size)
            offset = 0
            for m in src.mipmaps:
                data[offset:offset+m.size] = src.mipmap_data(m)
                offset += m.size

            return data

        elif st is ImageSource.Uncompressed:
            return src

        elif st is ImageSource.EnvCubemap:
            return src.data_buffer

        else:
            raise NotImplementedError(f"Texture data function not implemented for image of type {st}")

    def iter_mipmaps(self):
        src, st = self.source, self.source_type

        if st is ImageSource.Ktx:
            offset = 0
            for mipmap in src.mipmaps:
                # Fix to work with cubemaps ( In Vulkan, cubemap faces are interpreted as array layers )
                layer = mipmap.layer + mipmap.face

                yield MipmapData(mipmap.index, layer, offset, mipmap.size, mipmap.width, mipmap.height)
                offset += mipmap.size

        elif st is ImageSource.Uncompressed:
            width, height, depth = self.extent
            yield MipmapData(0, 0, 0, self.texture_size, width, height)

        elif st is ImageSource.EnvCubemap:
            for mipmap in src.mipmaps:
                layer = mipmap.face
                yield MipmapData(mipmap.index, layer, mipmap.offset, mipmap.size, mipmap.width, mipmap.height)

        else:
            raise NotImplementedError(f"Mipmaps function not implemented for image of type {st}")

    def size(self):
        return self.texture_size

    def __len__(self):
        return self.mipmaps_levels

    def __getitem__(self, key):
        if not isinstance(key, int) and not isinstance(key, slice):
            raise ValueError("Image mipmap index must be int or slice")

        src, st = self.source, self.source_type
        if st is ImageSource.Ktx:
            return Image.from_ktx(src[key])
        else:
            raise NotImplementedError(f"Indexing is not implemented for image of type {st}")
        
    @staticmethod
    def _uncompressed_image_size(extent, fmt):
        w, h, d = extent
        pixel_count = w*h*d
        pixel_size = IMAGE_FORMAT_PIXEL_SIZE.get(fmt)
        if pixel_size is None:
            raise ValueError(f"Pixel size for format {fmt} is not defined")

        return pixel_count * pixel_size
    