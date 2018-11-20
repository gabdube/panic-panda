from vulkan import vk, helpers as hvk
from .data_shader import DataShader
from .data_mesh import DataMesh
from .data_game_object import DataGameObject


class DataScene(object):

    def __init__(self, engine, scene):
        self.engine = engine
        self.scene = scene

        self.command_pool = None
        self.render_commands = None
        self.render_cache = {}

        self.shaders = None
        self.objects = None
        self.pipelines = None
        self.pipeline_cache = None

        self.meshes_alloc = None
        self.meshes_buffer = None
        self.meshes = None

        self._setup_shaders()
        self._setup_objects()
        self._setup_pipelines()
        self._setup_render_commands()
        self._setup_render_cache()

    def free(self):
        engine, api, device = self.ctx
        mem = engine.memory_manager

        for pipeline in self.pipelines:
            hvk.destroy_pipeline(api, device, pipeline)
        
        hvk.destroy_pipeline_cache(api, device, self.pipeline_cache)
        hvk.destroy_buffer(api, device, self.meshes_buffer)
        mem.free_alloc(self.meshes_alloc)

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
        # Caching things locally to improve lookup speed
        h = hvk

        engine, api, device = self.ctx
        render_command = self.render_commands[framebuffer_index]
        rc = self.render_cache

        pipelines = self.pipelines
        pipeline_index = None

        shaders = self.shaders
        meshes = self.meshes
        meshes_buffer = self.meshes_buffer
        
        # Render pass begin setup
        render_pass_begin = rc["render_pass_begin_info"]
        render_pass_begin.framebuffer = engine.render_target.framebuffers[framebuffer_index]

        extent = rc["render_area_extent"]
        extent.width, extent.height = engine.info["swapchain_extent"].values()

        # Recording
        h.begin_command_buffer(api, render_command, rc["begin_info"])
        h.begin_render_pass(api, render_command, render_pass_begin, vk.SUBPASS_CONTENTS_INLINE)

        for obj in self.objects:
            if obj.pipeline is not None and pipeline_index != obj.pipeline:
                pipeline_index = obj.pipeline
                hvk.bind_pipeline(api, render_command, pipelines[pipeline_index], vk.PIPELINE_BIND_POINT_GRAPHICS)

            if obj.mesh is not None:
                mesh = meshes[obj.mesh]
                shader = shaders[obj.shader]

                attributes_buffer = [meshes_buffer] * len(mesh.attribute_offsets)
                attribute_offsets = mesh.attribute_offsets_for_shader(shader)

                h.bind_index_buffer(api, render_command, meshes_buffer, mesh.indices_offset, mesh.indices_type)
                h.bind_vertex_buffers(api, render_command, attributes_buffer, attribute_offsets)

                h.draw_indexed(api, render_command, mesh.indices_count)

        h.end_render_pass(api, render_command)
        h.end_command_buffer(api, render_command)

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

        staging_mesh_offset = 0
        mesh_cache_lookup = []
        data_meshes = []
        data_objects = []

        for obj in scene.objects:
            mesh = meshes[obj.mesh]
            if mesh is not None and id(mesh) not in mesh_cache_lookup:
                mesh_cache_lookup.append(id(mesh))
                data_meshes.append(DataMesh(mesh, staging_mesh_offset))
                staging_mesh_offset += mesh.size()

            data_objects.append(DataGameObject(obj))

        staging_alloc, staging_buffer = self._setup_staging(staging_mesh_offset, data_meshes)
        meshes_alloc, meshes_buffer = self._setup_resources(staging_alloc, staging_buffer, data_meshes)

        self.meshes_alloc = meshes_alloc
        self.meshes_buffer = meshes_buffer
        self.meshes = data_meshes
        self.objects = data_objects

        hvk.destroy_buffer(api, device, staging_buffer)
        mem.free_alloc(staging_alloc)

    def _setup_pipelines(self):
        engine, api, device = self.ctx
        shaders = self.shaders
        rt = engine.render_target
        
        assembly = hvk.pipeline_input_assembly_state_create_info()
        raster = hvk.pipeline_rasterization_state_create_info()
        multisample = hvk.pipeline_multisample_state_create_info()

        width, height = engine.info["swapchain_extent"].values()
        viewport = hvk.viewport(width=width, height=height)
        render_area = hvk.rect_2d(0, 0, width, height)
        viewport = hvk.pipeline_viewport_state_create_info(
            viewports=(viewport,),
            scissors=(render_area,)
        )

        depth_stencil = hvk.pipeline_depth_stencil_state_create_info(
            depth_test_enable = vk.TRUE,
            depth_write_enable  = vk.TRUE,
            depth_compare_op = vk.COMPARE_OP_LESS_OR_EQUAL,
        )

        color_blend = hvk.pipeline_color_blend_state_create_info(
            attachments = (hvk.pipeline_color_blend_attachment_state(),)
        )

        grouped_objects = self._group_objects_by_shaders()
        pipeline_infos = []
        for shader_index, objects in grouped_objects:
            shader = shaders[shader_index]
            
            for obj in objects:
                obj.pipeline = shader_index
  
            info = hvk.graphics_pipeline_create_info(
                stages = shader.stage_infos,
                vertex_input_state = shader.vertex_input_state,
                input_assembly_state = assembly,
                viewport_state = viewport,
                rasterization_state = raster,
                multisample_state = multisample,
                depth_stencil_state = depth_stencil,
                color_blend_state = color_blend,
                layout = shader.pipeline_layout,
                render_pass = rt.render_pass
            )

            pipeline_infos.append(info)
  

        self.pipeline_cache = hvk.create_pipeline_cache(api, device, hvk.pipeline_cache_create_info())
        self.pipelines = hvk.create_graphics_pipelines(api, device, pipeline_infos, self.pipeline_cache)

    def _group_objects_by_shaders(self):
        groups = []
        shaders_index = []

        for obj in self.objects:
            if obj.shader in shaders_index:
                i = shaders_index.index(obj.shader)
                groups[i][1].append(obj)
            else:
                groups.append((obj.shader, [obj]))

        return groups

    def _setup_staging(self, meshes_size, data_meshes):
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

        with mem.map_alloc(staging_alloc) as alloc:
            for dm in data_meshes:
                alloc.write_bytes(dm.base_offset, dm.as_bytes())

       
        return staging_alloc, staging_buffer

    def _setup_resources(self, staging_alloc, staging_buffer, data_meshes):
        engine, api, device = self.ctx
        mem = engine.memory_manager
        cmd = engine.setup_command_buffer

        # Final buffer allocation
        mesh_buffer = hvk.create_buffer(api, device, hvk.buffer_create_info(
            size = staging_alloc.size, 
            usage = vk.BUFFER_USAGE_INDEX_BUFFER_BIT | vk.BUFFER_USAGE_VERTEX_BUFFER_BIT | vk.BUFFER_USAGE_TRANSFER_DST_BIT
        ))
        mesh_alloc = mem.alloc(mesh_buffer, vk.STRUCTURE_TYPE_BUFFER_CREATE_INFO, (vk.MEMORY_PROPERTY_DEVICE_LOCAL_BIT,))

        # Uploading commands
        region = vk.BufferCopy(src_offset=0, dst_offset=0, size=staging_alloc.size)
        regions = (region,)

        hvk.begin_command_buffer(api, cmd, hvk.command_buffer_begin_info())
        hvk.copy_buffer(api, cmd, staging_buffer, mesh_buffer, regions)
        hvk.end_command_buffer(api, cmd)

        # Submitting
        engine.submit_setup_command(wait=True)

        return mesh_alloc, mesh_buffer

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
            command_buffer_count = render_target.framebuffer_count,
            level = vk.COMMAND_BUFFER_LEVEL_PRIMARY
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
                hvk.clear_value(color=(0.1, 0.1, 0.1, 1.0)),
                hvk.clear_value(depth=1.0, stencil=0)
            )
        )

        self.render_cache["render_pass_begin_info"] = render_pass_begin
        self.render_cache["render_area_extent"] = render_pass_begin.render_area.extent

