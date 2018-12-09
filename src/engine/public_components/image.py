from ..base_types import name_generator
from ..assets import KTXFile, IMAGE_PATH
from vulkan import vk, helpers as hvk
from collections import namedtuple
from enum import Enum
from pathlib import Path


MipmapData = namedtuple('MipmapData', ('level', 'layer', 'offset', 'size', 'width', 'height'))
CombinedImageSampler = namedtuple("CombinedImageSampler", ("image_id", "view_name", "sampler_id"))
image_name = name_generator("Image")


class ImageSource(Enum):
    Ktx = 0
    Array = 15
    ArrayCube = 16


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

    def __init__(self, **kwargs):
        self.id = None
        self.name = kwargs.get('name', next(image_name))
        
        self.views = {}

        self.source_type = None
        self.source_sub_type = None
        self.source = None

        self.flags = 0
        self.format = None
        self.extent = None
        self.mipmaps_levels = None
        self.array_layers = 1
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

    @classmethod
    def from_cubemap_directory(cls, path, name, opener, **kwargs):
        
        def check_mismatch(obj, member, value):
            obj_value = getattr(obj, member)
            if obj_value is None:
                setattr(obj, member, value)
            elif obj_value != value:
                raise ValueError(f"{member} mismatch between two files: {obj_value} / {value}")

        image = super().__new__(cls)
        image.__init__(**kwargs)

        image.source_type = ImageSource.ArrayCube
        image.flags = vk.IMAGE_CREATE_CUBE_COMPATIBLE_BIT
        image.array_layers = 6
        image.source = src = []
        image.texture_size = 0
    
        if opener is KTXFile:
            image.source_sub_type = ImageSource.Ktx
            ext = "ktx"
        else:
            raise NotImplementedError(f"Opener {opener} is not recognized")

        start = len(str(IMAGE_PATH))+1
        for p in Path(IMAGE_PATH / path).glob(f"{name}*.{ext}"):
            file_path = str(p)[start::]
            f = opener.open(file_path)

            check_mismatch(image, "format", f.format)
            check_mismatch(image, "extent", (f.width, f.height, f.depth))
            check_mismatch(image, "mipmaps_levels", f.mips_level)
            image.texture_size += len(f.data)

            src.append(f)

        if len(src) != 6:
            raise ValueError(f"A cubemap must have 6 faces but {len(src)} faces were found.")

        # Order the sources by the cubeface ids
        faces = ImageCubemapFaces
        faces = (("_back_", faces.Back), ("_bottom_", faces.Bottom), ("_front_", faces.Front), 
                 ("_left_", faces.Left), ("_right_", faces.Right), ("_top_", faces.Top))

        def by_cube_face(f):
            file_name = f.file_name.lower()
            face = next((face for face_name, face in faces if face_name in file_name), None)
            if face is None:
                raise ValueError(f"Impossible to find cubemap face from filename {file_name}.")

            return face.value

        src.sort(key=by_cube_face)

        # Generate a default view
        if kwargs.get("nodefault", False) != True:
            subs_range = hvk.image_subresource_range(level_count = image.mipmaps_levels, layer_count = 6)
            image.views["default"] = ImageView.from_params(
                view_type=vk.IMAGE_VIEW_TYPE_CUBE,
                format=image.format,
                subresource_range=subs_range
            )

        return image

    def mipmaps(self):
        src, st, sst = self.source, self.source_type, self.source_sub_type
        total_offset, layer = 0, 0

        if st is ImageSource.Ktx:
            for mipmap in src.mipmaps:
                yield MipmapData(mipmap.level, layer, mipmap.offset, mipmap.size, mipmap.width, mipmap.height)
        elif st is ImageSource.ArrayCube or st is ImageSource.Array:
            if sst is ImageSource.Ktx:
                for sub_src in src:
                    for mipmap in sub_src.mipmaps:
                        yield MipmapData(mipmap.level, layer, total_offset+mipmap.offset, mipmap.size, mipmap.width, mipmap.height)
                    
                    layer += 1
                    total_offset += len(sub_src.data)
        else:
            raise NotImplementedError(f"Mipmaps function not implemented for image of type {st}")

    def size(self):
        return self.texture_size


