from vulkan import vk, helpers as hvk
from .data_shader import DataShader


class DataScene(object):

    def __init__(self, engine, scene):
        self.engine = engine
        self.scene = scene

        self.command_pool = None
        self.render_commands = None
        self.render_cache = {}

        self.shaders = None

        self.mesh_alloc = None
        self.mesh_buffer = None
        self.meshes = None

        self._setup_shaders()
        self._setup_objects()
        self._setup_render_commands()
        self._setup_render_cache()

    def free(self):
        engine, api, device = self.ctx

        for shader in self.shaders:
            shader.free()

        hvk.destroy_command_pool(api, device, self.command_pool)

        del self.engine
        del self.scene
        del self.shaders

    @property
    def ctx(self):
        engine = self.engine
        api, device = engine.api, engine.device
        return engine, api, device

    def record(self, framebuffer_index):
        engine, api, device = self.ctx
        render_command = self.render_commands[framebuffer_index]
        rc = self.render_cache
        
        render_pass_begin = rc["render_pass_begin_info"]
        render_pass_begin.framebuffer = engine.render_target.framebuffers[framebuffer_index]

        extent = rc["render_area_extent"]
        extent.width, extent.height = engine.window.dimensions()

        hvk.begin_command_buffer(api, render_command, rc["begin_info"])
        hvk.begin_render_pass(api, render_command, render_pass_begin, vk.SUBPASS_CONTENTS_SECONDARY_COMMAND_BUFFERS)

        hvk.end_render_pass(api, render_command)
        hvk.end_command_buffer(api, render_command)

    def _setup_shaders(self):
        e = self.engine

        shaders = []
        for shader in self.scene.shaders:
            shaders.append(DataShader(e, shader))

        self.shaders = shaders

    def _setup_objects(self):
        engine, api, device = self.ctx
        mem = engine.memory_manager

        scene = self.scene
        meshes = scene.meshes

        total_mesh_size = 0
        mesh_cache_lookup = []

        for obj in scene.objects:
            mesh = meshes[obj.mesh]
            if mesh is not None and id(mesh) not in mesh_cache_lookup:
                total_mesh_size += mesh.size()
                mesh_cache_lookup.append(id(mesh))

        staging_alloc, staging_buffer = self._setup_staging(total_mesh_size, meshes)
        meshes_alloc, meshes_buffer = self._setup_resources(
            total_mesh_size,
            vk.BUFFER_USAGE_INDEX_BUFFER_BIT | vk.BUFFER_USAGE_VERTEX_BUFFER_BIT,
            (vk.MEMORY_PROPERTY_DEVICE_LOCAL_BIT,)
        )


        hvk.destroy_buffer(api, device, staging_buffer)
        mem.free_alloc(staging_alloc)

    def _setup_staging(self, meshes_size, meshes):
        engine, api, device = self.ctx
        mem = engine.memory_manager

        staging_buffer = hvk.create_buffer(api, device, hvk.buffer_create_info(
            size = meshes_size,
            usage = vk.BUFFER_USAGE_TRANSFER_SRC_BIT
        ))
        staging_alloc = mem.alloc(
            staging_buffer, 
            vk.STRUCTURE_TYPE_BUFFER_CREATE_INFO, 
            (vk.MEMORY_PROPERTY_HOST_COHERENT_BIT | vk.MEMORY_PROPERTY_HOST_VISIBLE_BIT,)
        )

        return staging_alloc, staging_buffer

    def _setup_resources(self, total_size, usage, alloc_types):
        engine, api, device = self.ctx
        mem = engine.memory_manager

        buffer = hvk.create_buffer(api, device, hvk.buffer_create_info(size = total_size, usage = usage))
        alloc = mem.alloc(buffer,  vk.STRUCTURE_TYPE_BUFFER_CREATE_INFO, alloc_types)


        return buffer, alloc

    def _setup_render_commands(self):
        engine, api, device = self.ctx
        render_queue = engine.render_queue
        render_target = engine.render_target

        command_pool = hvk.create_command_pool(api, device, hvk.command_pool_create_info(
            queue_family_index = render_queue.family.index,
            flags = vk.COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT
        ))

        cmd_draw = hvk.allocate_command_buffers(api, device, hvk.command_buffer_allocate_info(
            command_pool = command_pool,
            command_buffer_count = render_target.framebuffer_count
        ))

        self.command_pool = command_pool
        self.render_commands = cmd_draw

    def _setup_render_cache(self):
        self.render_cache["begin_info"] = hvk.command_buffer_begin_info()

        render_pass_begin = hvk.render_pass_begin_info(
            render_pass = self.engine.render_target.render_pass,
            framebuffer = 0,
            render_area = hvk.rect_2d(0, 0, 0, 0),
            clear_values = (
                hvk.clear_value(color=(0.2, 0.2, 0.2, 1.0)),
                hvk.clear_value(depth=1.0, stencil=0)
            )
        )

        self.render_cache["render_pass_begin_info"] = render_pass_begin
        self.render_cache["render_area_extent"] = render_pass_begin.render_area.extent

