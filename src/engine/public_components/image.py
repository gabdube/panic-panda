from ..base_types import name_generator
from enum import Enum


image_name = name_generator("Image")


class Image(object):

    def __init__(self, **kwargs):
        self.id = None
        self.name = kwargs.get('name', next(image_name))
        
        self.source_type = None
        self.source = None

        self.texture_size = None

    @classmethod
    def from_ktx(cls, ktx_file, **kwargs):
        image = super().__new__(cls)
        image.__init__(**kwargs)

        image.source_type = ImageSource.Ktx
        image.source = ktx_file

        image.texture_size = len(ktx_file.data)

        return image

    def size(self):
        return self.texture_size


class ImageSource(Enum):
    Ktx = 0
