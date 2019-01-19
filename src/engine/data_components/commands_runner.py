from .. import DeviceCommand, DeviceCommandEnum
from vulkan import vk, helpers as hvk


class CommandsRunner(object):

    @staticmethod
    def run_device(command_list, api, cmd_buffer, data_scene):
        maps = DEVICE_FUNCTIONS_MAP
        for cmd in command_list:
            maps[cmd.cmd_type](api, cmd_buffer, cmd.data, data_scene)
            
    @staticmethod
    def run_app(command_list, data_scene):
        maps = APP_FUNCTIONS_MAP
        for cmd in command_list:
            maps[cmd.cmd_type](cmd.data, data_scene)

    @staticmethod
    def device_update_image_layout(api, cmd_buffer, cmd_data, data_scene):
        data_image = data_scene.images[cmd_data["image_id"]]
        image = data_image.image

        data_image.update_layout(cmd_data["new_layout"])
        dst_stage_mask = hvk.dst_stage_mask_for_access_mask(data_image.target_access_mask)

        change_layout = hvk.image_memory_barrier(
            image = data_image.image_handle,
            old_layout = data_image.layout,
            new_layout = data_image.target_layout,
            src_access_mask = data_image.access_mask,
            dst_access_mask = data_image.target_access_mask,
            subresource_range = hvk.image_subresource_range(
                level_count = image.mipmaps_levels,
                layer_count = image.array_layers
            )
        )

        hvk.pipeline_barrier(api, cmd_buffer, (change_layout,), dst_stage_mask=dst_stage_mask)

    @staticmethod
    def app_update_image_layout(cmd_data, data_scene):
        data_image = data_scene.images[cmd_data["image_id"]]
        data_image.layout = data_image.target_layout
        data_image.access_mask = data_image.target_access_mask


DEVICE_FUNCTIONS_MAP = {
    DeviceCommandEnum.UpdateImageLayout: CommandsRunner.device_update_image_layout
}

APP_FUNCTIONS_MAP = {
    DeviceCommandEnum.UpdateImageLayout: CommandsRunner.app_update_image_layout
}
