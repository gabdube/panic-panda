from enum import Enum


class DeviceCommandList(list):
    
    def __init__(self, *items):
        for i in items:
            if not isinstance(i, DeviceCommand):
                raise TypeError(f"Item type must be DeviceCommand, got {type(i)}")

        super().__init__(items)


class DeviceCommand(object):
    
    def __init__(self, cmd_type, **data):
        self.cmd_type = cmd_type
        self.data = data

    @staticmethod
    def update_image_layout(image_id, new_layout):
        return DeviceCommand(DeviceCommandEnum.UpdateImageLayout, image_id=image_id, new_layout=new_layout)


class DeviceCommandEnum(Enum):
    UpdateImageLayout = 0
