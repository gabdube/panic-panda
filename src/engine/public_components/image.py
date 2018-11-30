from ..base_types import name_generator

mesh_name = name_generator("Image")


class Image(object):

    def __init__(self, **kwargs):
        self.id = None
        self.name = kwargs.get('name', next(mesh_name))

    @classmethod
    def from_ktx(cls, ktx_file, **kwargs):
        image = super().__new__(cls)
        image.__init__(**kwargs)

        return image
