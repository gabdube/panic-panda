from enum import IntFlag
from collections import OrderedDict
from system import Window, events as evt
from vulkan import vk, helpers as hvk
from . import Queue, ImageAndView
from .memory_manager import MemoryManager
from .render_target import RenderTarget
from .renderer import Renderer
from .data_components import DataScene

# Tells the engine to instantiate a Debugger object that will logs various vulkan information 
DEBUG = __debug__
if DEBUG:
    try:
        from PyQt5.QtWidgets import QApplication
        from .debug_ui import DebugUI
    except ImportError:
        DebugUI = lambda app: print("PYQT5 not found. Debug UI will not be available")
else:
    DebugUI = lambda app: None


class Engine(object):

    def __init__(self):
        self.window = w = Window(width=800, height=600)

        self.running = False

        self.api = self.instance = self.device = self.physical_device = None
        self.debugger = self.debug_ui = self.surface = self.render_queue = None
        self.swapchain = self.swapchain_images = None
        self.command_pool = self.setup_command_buffer = self.setup_fence = None
        self.info = {}

        self.graph = []
        self.current_scene_index = None

        self._setup_instance()
        self._setup_debugger()
        self._setup_surface()
        self._setup_device()
        self._setup_device_info()
        self._setup_swapchain()
        self._setup_setup_commands()

        self.memory_manager = MemoryManager(self)
        self.render_target = RenderTarget(self)

        self.renderer = Renderer(self)

    def free(self):
        api, i, d = self.api, self.instance, self.device

        hvk.device_wait_idle(api, d)

        hvk.destroy_command_pool(api, d, self.command_pool)
        hvk.destroy_fence(api, d, self.setup_fence)

        for scene in self.graph:
            scene.free()

        self.renderer.free()
        self.render_target.free()
        self.memory_manager.free()

        hvk.destroy_swapchain(api, d, self.swapchain)
        hvk.destroy_device(api, d)

        hvk.destroy_surface(api, i, self.surface)

        if self.debugger is not None:
            self.debugger.stop()

        if self.debug_ui is not None:
            self.debug_ui.close()

        hvk.destroy_instance(api, i)

        self.window.destroy()

    def load(self, scene):
        if scene.loaded:
            return

        scene_data = DataScene(self, scene)
        scene.id = len(self.graph)
        scene.on_initialized()
        self.graph.append(scene_data)

    def activate(self, scene):
        assert scene.id is not None, "Scene was not loaded in engine"

        # Skip any setup events in the system event queue
        w = self.window
        w.show()
        w.translate_system_events()
        w.events.clear()

        self.running = True
        self.current_scene_index = scene.id

        if self.debug_ui is not None:
            scene_data = self.graph[scene.id]
            self.debug_ui.load_scene(scene_data)

    def update(self):
        scene_data = self.graph[self.current_scene_index]
        scene_data.apply_updates()

    def events(self):
        scene_data = self.graph[self.current_scene_index]
        scene = scene_data.scene
        e, w = evt, self.window

        w.translate_system_events()

        for event, data in w.events:
            if event is e.MouseMove:
                scene.on_mouse_move(event, data)
            elif event is e.MouseClick:
                scene.on_mouse_click(event, data)
            elif event is e.MouseScroll:
                scene.on_mouse_scroll(event, data)
            elif event is e.KeyPress:
                scene.on_key_pressed(event, data)
            elif event is e.WindowResized:
                self._update_swapchain(data)

        if self.debug_ui is not None:
            self.debug_ui.events()

        if w.must_exit:
            self.running = False

    def render(self):
        scene_data = self.graph[self.current_scene_index]
        self.renderer.render(scene_data)

    def submit_setup_command(self, wait=False):
        api, device = self.api, self.device
        fence = 0

        if wait:
            fence = self.setup_fence

        infos = (hvk.submit_info(command_buffers=(self.setup_command_buffer,)),)
        hvk.queue_submit(api, self.render_queue.handle, infos, fence)

        if wait:
            f = (fence,)
            hvk.wait_for_fences(api, device, f)
            hvk.reset_fences(api, device, f)

    # Setup functions

    def _setup_instance(self):
        layers = []
        extensions = ["VK_KHR_surface", hvk.SYSTEM_SURFACE_EXTENSION]

        if DEBUG:
            extensions.append("VK_EXT_debug_utils")
            layers.append("VK_LAYER_LUNARG_standard_validation")

        self.api, self.instance = hvk.create_instance(extensions, layers)

    def _setup_debugger(self):
        from vulkan.debugger import Debugger

        if not DEBUG:
            self.debugger = None
            return

        self.debugger = Debugger(self.api, self.instance)
        self.debugger.start()    

        self.debug_ui = DebugUI(self)

    def _setup_surface(self):
        self.surface = hvk.create_surface(self.api, self.instance, self.window)
    
    def _setup_device(self):
        api, instance = self.api, self.instance

        # Device selection (use the first available)
        physical_devices = hvk.list_physical_devices(api, instance)
        self.physical_device = physical_device = physical_devices[0]

        # Get the features
        supported_features = hvk.physical_device_features(api, physical_device)
        if not "texture_compression_BC" in supported_features:
            raise RuntimeError("BC compressed textures are not supported on your machine")
        
        features = vk.PhysicalDeviceFeatures(texture_compression_BC = 1)

        # Queues setup (A single graphic queue)
        queue_families = hvk.list_queue_families(api, physical_device)

        render_queue_family = None
        for qf in queue_families:
            if qf.properties.queue_flags & vk.QUEUE_GRAPHICS_BIT != 0:
                render_queue_family = qf
        
        render_queue_create_info = hvk.queue_create_info(
            queue_family_index = render_queue_family.index,
            queue_count = 1
        )

        # Device creation
        extensions = ("VK_KHR_swapchain",)
        self.device = device = hvk.create_device(api, physical_device, extensions, (render_queue_create_info,), features)

        # Queue setup
        render_queue_handle = hvk.get_queue(api, device, render_queue_family.index, 0)
        self.render_queue = Queue(render_queue_handle, render_queue_family)

    def _setup_device_info(self):
        api, physical_device = self.api, self.physical_device
        info = self.info

        properties = hvk.physical_device_properties(api, physical_device)
        info["limits"] = properties.limits

        depth_formats = (vk.FORMAT_D32_SFLOAT_S8_UINT, vk.FORMAT_D24_UNORM_S8_UINT, vk.FORMAT_D16_UNORM_S8_UINT)
        for fmt in depth_formats:
            prop = hvk.physical_device_format_properties(api, physical_device, fmt)
            if vk.FORMAT_FEATURE_DEPTH_STENCIL_ATTACHMENT_BIT & prop.optimal_tiling_features != 0:
                info["depth_format"] = fmt
                break

        if "depth_format" not in info:
            raise RuntimeError("Failed to find a suitable depth stencil format.")

    def _setup_swapchain(self):
        api, device, physical_device, surface = self.api, self.device, self.physical_device, self.surface
        render_queue = self.render_queue
        old_swapchain = self.swapchain

        # Swapchain Setup
        caps = hvk.physical_device_surface_capabilities(api, physical_device, surface)
        formats = hvk.physical_device_surface_formats(api, physical_device, surface)
        present_modes = hvk.physical_device_surface_present_modes(api, physical_device, surface)

        if not hvk.get_physical_device_surface_support(api, physical_device, surface, render_queue.family.index):
            raise RuntimeError("Main rendering queue cannot present images to the surface")

        # Swapchain Format
        format_values = tuple(vkf.format for vkf in formats)
        required_formats = [vk.FORMAT_B8G8R8A8_SRGB, vk.FORMAT_B8G8R8A8_UNORM]
        for i, required_format in enumerate(required_formats):
            if required_format in format_values:
                required_formats[i] = format_values.index(required_format)
            else:
                required_formats[i] = None

        selected_format = next((formats[i] for i in required_formats if i is not None), None)
        if selected_format is None:
            raise RuntimeError("Required swapchain image format not supported")

        # Swapchain Extent
        extent = caps.current_extent
        if extent.width == -1 or extent.height == -1:
            width, height = self.window.dimensions()
            extent.width = width
            extent.height = height

        # Min image count
        min_image_count = 2
        if caps.max_image_count != 0 and caps.max_image_count < min_image_count:
            raise RuntimeError("Minimum image count not met")
        elif caps.min_image_count > min_image_count:
            min_image_count = caps.min_image_count

        # Present mode
        present_mode = vk.PRESENT_MODE_FIFO_KHR
        if vk.PRESENT_MODE_MAILBOX_KHR in present_modes:
            present_mode = vk.PRESENT_MODE_MAILBOX_KHR
        elif vk.PRESENT_MODE_IMMEDIATE_KHR in present_modes:
            present_mode = vk.PRESENT_MODE_IMMEDIATE_KHR

        # Default image transformation
        transform = caps.current_transform
        if vk.SURFACE_TRANSFORM_IDENTITY_BIT_KHR in IntFlag(caps.supported_transforms):
            transform = vk.SURFACE_TRANSFORM_IDENTITY_BIT_KHR

        # Swapchain creation
        old_swapchain = old_swapchain or 0
        swapchain_image_format = selected_format.format
        self.swapchain = hvk.create_swapchain(api, device, hvk.swapchain_create_info(
            surface = surface,
            image_format = swapchain_image_format,
            image_color_space = selected_format.color_space,
            image_extent = extent,
            min_image_count = min_image_count,
            present_mode = present_mode,
            pre_transform = transform,
            image_usage = vk.IMAGE_USAGE_COLOR_ATTACHMENT_BIT | vk.IMAGE_USAGE_TRANSFER_DST_BIT,
            old_swapchain = old_swapchain
        ))

        hvk.destroy_swapchain(api, device, old_swapchain)

        self.info["swapchain_extent"] = OrderedDict(width=extent.width, height=extent.height)
        self.info["swapchain_format"] = swapchain_image_format

    def _setup_setup_commands(self):
        api, device = self.api, self.device
        render_queue = self.render_queue

        command_pool = hvk.create_command_pool(api, device, hvk.command_pool_create_info(
            queue_family_index = render_queue.family.index,
            flags = vk.COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT
        ))

        cmds = hvk.allocate_command_buffers(api, device, hvk.command_buffer_allocate_info(
            command_pool = command_pool,
            command_buffer_count = 1
        ))

        fence_info = hvk.fence_create_info()
        fence = hvk.create_fence(api, device, fence_info)


        self.command_pool = command_pool
        self.setup_command_buffer = cmds[0]
        self.setup_fence = fence

    # Update functions

    def _update_swapchain(self, resize_data):
        hvk.device_wait_idle(self.api, self.device)
        self._setup_swapchain()
        self.render_target._update_swapchain()
        self.renderer._setup_render_cache()
        self.graph[self.current_scene_index]._setup_render_cache()
