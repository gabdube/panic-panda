from vulkan import vk, helpers as hvk
from .data_shader import DataShader
from .data_mesh import DataMesh
from .data_image import DataImage
from .data_game_object import DataGameObject
from ctypes import sizeof, memset


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
        self.descriptor_pool = None

        self.shader_objects = None
        self.shader_objects_sorted = False

        self.meshes_alloc = None
        self.meshes_buffer = None
        self.meshes = None

        self.images_alloc = None
        self.images = None

        self.uniforms_alloc = None
        self.uniforms_buffer = None

        self._setup_shaders()
        self._setup_objects()
        self._setup_pipelines()
        self._setup_descriptor_sets_pool()
        self._setup_descriptor_sets()
        self._setup_descriptor_write_sets()
        self._setup_render_commands()
        self._setup_render_cache()

    def free(self):
        engine, api, device = self.ctx
        mem = engine.memory_manager

        hvk.destroy_buffer(api, device, self.uniforms_buffer)
        mem.free_alloc(self.uniforms_alloc)

        hvk.destroy_descriptor_pool(api, device, self.descriptor_pool)

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
        cmd = self.render_commands[framebuffer_index]
        rc = self.render_cache

        pipelines = self.pipelines
        pipeline_index = None

        shaders = self.shaders
        current_shader_index = None
        current_shader = None

        meshes = self.meshes
        meshes_buffer = self.meshes_buffer
        
        # Render pass begin setup
        render_pass_begin = rc["render_pass_begin_info"]
        render_pass_begin.framebuffer = engine.render_target.framebuffers[framebuffer_index]

        extent = rc["render_area_extent"]
        extent.width, extent.height = engine.info["swapchain_extent"].values()

        viewports = rc["viewports"]
        scissors = rc["scissors"]

        # Recording
        h.begin_command_buffer(api, cmd, rc["begin_info"])
        h.begin_render_pass(api, cmd, render_pass_begin, vk.SUBPASS_CONTENTS_INLINE)

        for obj in self.objects:

            if obj.pipeline is not None and pipeline_index != obj.pipeline:
                pipeline_index = obj.pipeline
                hvk.bind_pipeline(api, cmd, pipelines[pipeline_index], vk.PIPELINE_BIND_POINT_GRAPHICS)
                hvk.set_viewport(api, cmd, viewports)
                hvk.set_scissor(api, cmd, scissors)

            if obj.shader is not None and current_shader_index != obj.shader:
                current_shader_index = obj.shader
                current_shader = shaders[obj.shader]
                hvk.bind_descriptor_sets(api, cmd, vk.PIPELINE_BIND_POINT_GRAPHICS, current_shader.pipeline_layout, current_shader.descriptor_sets)

            if obj.descriptor_sets is not None:
                hvk.bind_descriptor_sets(api, cmd, vk.PIPELINE_BIND_POINT_GRAPHICS, current_shader.pipeline_layout, obj.descriptor_sets, firstSet=len(current_shader.descriptor_sets))

            if obj.mesh is not None:
                mesh = meshes[obj.mesh]
                shader = shaders[obj.shader]

                attributes_buffer = [meshes_buffer] * len(mesh.attribute_offsets)
                attribute_offsets = mesh.attribute_offsets_for_shader(shader)

                h.bind_index_buffer(api, cmd, meshes_buffer, mesh.indices_offset, mesh.indices_type)
                h.bind_vertex_buffers(api, cmd, attributes_buffer, attribute_offsets)

                h.draw_indexed(api, cmd, mesh.indices_count)

        h.end_render_pass(api, cmd)
        h.end_command_buffer(api, cmd)

    def apply_updates(self):
        scene = self.scene
        data_objects = self.objects
        data_shaders = self.shaders
        obj_update, shader_update = [], []

        for obj in scene.update_obj_set:
            if len(obj.uniforms.updated_member_names) > 0:
                dobj = data_objects[obj.id]
                obj_update.append((obj, dobj))

        for shader in scene.update_shader_set:
            if len(shader.uniforms.updated_member_names) > 0:
                dshader = data_shaders[shader.id]
                shader_update.append((shader, dshader))

        if len(obj_update) > 0 or len(shader_update) > 0:
            self._update_uniforms(obj_update, shader_update)
            scene.update_obj_set.clear()
            scene.update_shader_set.clear()

    #
    # Setup things
    #

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
        shaders = self.shaders
        meshes = scene.meshes
        images = scene.images

        staging_mesh_offset = 0
        data_meshes, data_objects, data_images = [], [], []

        # Meshes setup
        for mesh in scene.meshes:
            data_mesh = DataMesh(mesh, staging_mesh_offset)
            data_meshes.append(data_mesh)
            staging_mesh_offset += mesh.size()
        
        # Images
        staging_image_offset = staging_mesh_offset
        for image in images:
            data_image = DataImage(image, staging_image_offset)
            data_images.append(data_image)
            staging_image_offset += image.size()

        # Objects setup
        for obj in scene.objects:

            if obj.shader is not None:
                shader = shaders[obj.shader]
                for layout in shader.local_layouts:
                    for name, struct in layout.struct_map.items():
                        setattr(obj.uniforms, name, struct())
                        obj.uniforms.uniform_names.append(name)
            
            data_objects.append(DataGameObject(obj))

        # Shader
        for shader, dshader in zip(scene.shaders, shaders):
            for layout in dshader.global_layouts:
                for name, struct in layout.struct_map.items():
                    setattr(shader.uniforms, name, struct())
                    shader.uniforms.uniform_names.append(name)

        staging_alloc, staging_buffer = self._setup_objects_staging(staging_image_offset, data_meshes, data_images)
        meshes_alloc, meshes_buffer = self._setup_meshes_resources(staging_alloc, staging_buffer, data_meshes)
        images_alloc = self._setup_images_resources(staging_alloc, data_images)

        self.meshes_alloc = meshes_alloc
        self.meshes_buffer = meshes_buffer
        self.meshes = data_meshes
        self.images_alloc = images_alloc
        self.images = data_images
        self.objects = data_objects

        hvk.destroy_buffer(api, device, staging_buffer)
        mem.free_alloc(staging_alloc)

    def _setup_objects_staging(self, staging_size, data_meshes, data_images):
        engine, api, device = self.ctx
        mem = engine.memory_manager

        staging_buffer = hvk.create_buffer(api, device, hvk.buffer_create_info(
            size = staging_size,
            usage = vk.BUFFER_USAGE_TRANSFER_SRC_BIT
        ))
        staging_alloc = mem.alloc(
            staging_buffer, 
            vk.STRUCTURE_TYPE_BUFFER_CREATE_INFO, 
            (vk.MEMORY_PROPERTY_HOST_COHERENT_BIT | vk.MEMORY_PROPERTY_HOST_VISIBLE_BIT,)
        )

        with mem.map_alloc(staging_alloc) as alloc:
            for dm in data_meshes:
                alloc.write_bytes(dm.base_offset, dm.as_ctypes_array())
            
            for di in data_images:
                alloc.write_bytes(di.base_offset, di.as_ctypes_array())
  
        return staging_alloc, staging_buffer

    def _setup_meshes_resources(self, staging_alloc, staging_buffer, data_meshes):
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

    def _setup_images_resources(self, staging_alloc, data_images):
        pass

    def _setup_pipelines(self):
        engine, api, device = self.ctx
        shaders = self.shaders
        rt = engine.render_target
        
        assembly = hvk.pipeline_input_assembly_state_create_info()
        raster = hvk.pipeline_rasterization_state_create_info()
        multisample = hvk.pipeline_multisample_state_create_info()
        viewport = hvk.pipeline_viewport_state_create_info(viewport_count=1, scissor_count=1)

        depth_stencil = hvk.pipeline_depth_stencil_state_create_info(
            depth_test_enable = vk.TRUE,
            depth_write_enable  = vk.TRUE,
            depth_compare_op = vk.COMPARE_OP_LESS_OR_EQUAL,
        )

        color_blend = hvk.pipeline_color_blend_state_create_info(
            attachments = (hvk.pipeline_color_blend_attachment_state(),)
        )

        dynamic_state = hvk.pipeline_dynamic_state_create_info(
            dynamic_states = (vk.DYNAMIC_STATE_VIEWPORT, vk.DYNAMIC_STATE_SCISSOR)
        )

        pipeline_infos = []
        for shader_index, objects in self._group_objects_by_shaders():
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
                dynamic_state = dynamic_state,
                layout = shader.pipeline_layout,
                render_pass = rt.render_pass
            )

            pipeline_infos.append(info)
  

        self.pipeline_cache = hvk.create_pipeline_cache(api, device, hvk.pipeline_cache_create_info())
        self.pipelines = hvk.create_graphics_pipelines(api, device, pipeline_infos, self.pipeline_cache)

    def _setup_descriptor_sets_pool(self):
        _, api, device = self.ctx
        shaders = self.shaders

        pool_sizes, max_sets = {}, 0

        for shader_index, objects in self._group_objects_by_shaders():
            shader = shaders[shader_index]
            object_count = len(objects)

            if shader.descriptor_set_layouts is None:
                continue

            for dset_layout in shader.local_layouts:
                for dtype, dcount in dset_layout.pool_size_counts:
                    if dtype in pool_sizes:
                        pool_sizes[dtype] += dcount * object_count
                    else:
                        pool_sizes[dtype] = dcount * object_count
            
                max_sets += object_count

            for dset_layout in shader.global_layouts:
                for dtype, dcount in dset_layout.pool_size_counts:
                    if dtype in pool_sizes:
                        pool_sizes[dtype] += dcount
                    else:
                        pool_sizes[dtype] = dcount
            
                max_sets += 1

        pool_sizes = tuple( vk.DescriptorPoolSize(type=t, descriptor_count=c) for t, c in pool_sizes.items() )
        pool = hvk.create_descriptor_pool(api, device, hvk.descriptor_pool_create_info(
            max_sets = max_sets,
            pool_sizes = pool_sizes
        ))

        self.descriptor_pool = pool

    def _setup_descriptor_sets(self):
        engine, api, device = self.ctx
        shaders = self.shaders
        descriptor_pool = self.descriptor_pool
        mem = engine.memory_manager

        uniforms_buffer_size = 0

        for shader_index, objects in self._group_objects_by_shaders():
            shader = shaders[shader_index]
            objlen = len(objects)
            
            # Uniforms buffer size
            uniforms_buffer_size += sum( l.struct_map_size_bytes for l in shader.local_layouts ) * objlen
            uniforms_buffer_size += sum( l.struct_map_size_bytes for l in shader.global_layouts )

            # Descriptor sets allocations
            set_layouts_global = [ l.set_layout for l in shader.global_layouts ]
            set_layouts_local = [ l.set_layout for l in shader.local_layouts ] * objlen
            descriptor_sets = hvk.allocate_descriptor_sets(api, device, hvk.descriptor_set_allocate_info(
                descriptor_pool = descriptor_pool,
                set_layouts = set_layouts_global + set_layouts_local
            ))

            # Save the global layouts to the shader
            shader.descriptor_sets = descriptor_sets[0: len(set_layouts_global)]

            # Save the local layouts to the objects
            step = len(tuple(shader.local_layouts))
            end = len(descriptor_sets)
            start = len(set_layouts_global)
            iter_objects = iter(objects)
            for i in range(start, end, step):
                obj = next(iter_objects)
                obj.descriptor_sets = descriptor_sets[i:i+step]


        # Uniform buffer creation
        uniforms_buffer = hvk.create_buffer(api, device, hvk.buffer_create_info(
            size = uniforms_buffer_size, 
            usage = vk.BUFFER_USAGE_UNIFORM_BUFFER_BIT
        ))
        uniforms_alloc = mem.alloc(
            uniforms_buffer,
            vk.STRUCTURE_TYPE_BUFFER_CREATE_INFO,
            (vk.MEMORY_PROPERTY_HOST_VISIBLE_BIT | vk.MEMORY_PROPERTY_HOST_COHERENT_BIT,)
        )

        # Make sure the uniforms are zeroed
        with mem.map_alloc(uniforms_alloc) as mapping:
            memset(mapping.pointer2, 0, uniforms_alloc.size)

        self.uniforms_alloc = uniforms_alloc
        self.uniforms_buffer = uniforms_buffer
        
    def _setup_descriptor_write_sets(self):
        _, api, device = self.ctx
        shaders = self.shaders
        uniform_buffer = self.uniforms_buffer
        uniform_offset = 0
        
        def generate_write_set(wst, descriptor_set):
            nonlocal uniform_buffer, uniform_offset
            dtype, drange, binding = wst['descriptor_type'], wst['range'], wst['binding']

            if dtype == vk.DESCRIPTOR_TYPE_UNIFORM_BUFFER:
                buffer_info = vk.DescriptorBufferInfo(
                    buffer = uniform_buffer,
                    offset = uniform_offset,
                    range = drange
                )

                write_set = hvk.write_descriptor_set(
                    dst_set = descriptor_set,
                    dst_binding = binding,
                    descriptor_type = dtype,
                    buffer_info = (buffer_info,)
                )

                uniform_offset += drange
            elif dtype == vk.DESCRIPTOR_TYPE_SAMPLED_IMAGE:
                sampler_image_info = vk.DescriptorImageInfo(
                    sampler = texture_sampler,
                    image_view = texture_view,
                    image_layout = texture_image_layout
                )

                write_set = hvk.write_descriptor_set(
                    dst_set = descriptor_set,
                    dst_binding = binding,
                    descriptor_type = dtype,
                    image_info = (sampler_image_info,)
                )
            else:
                raise ValueError(f"Unknown descriptor type: {dtype}")

            return write_set

        for shader_index, objects in self._group_objects_by_shaders():
            shader = shaders[shader_index]

            # Global descriptor sets
            shader.write_sets_update_infos = {}
            shader.write_sets = []
            for descriptor_set, descriptor_layout in zip(shader.descriptor_sets, shader.global_layouts):
                templates = descriptor_layout.write_set_templates
                shader.write_sets_update_infos.update({ wst["name"]: (uniform_offset, wst["range"]) for wst in templates })
                shader.write_sets.extend( generate_write_set(wst, descriptor_set) for wst in templates )

            hvk.update_descriptor_sets(api, device, shader.write_sets, ())

            # Local descriptor sets
            for obj in objects:
                obj.write_sets_update_infos = {}
                obj.write_sets = []

                for descriptor_set, descriptor_layout in zip(obj.descriptor_sets, shader.local_layouts):
                    templates = descriptor_layout.write_set_templates
                    obj.write_sets_update_infos.update({ wst["name"]: (uniform_offset, wst["range"]) for wst in templates })
                    obj.write_sets.extend( generate_write_set(wst, descriptor_set) for wst in templates )
                
                hvk.update_descriptor_sets(api, device, obj.write_sets, ())

    def _group_objects_by_shaders(self):
        if self.shader_objects_sorted:
            return self.shader_objects

        groups = []
        shaders_index = []

        for obj in self.objects:
            if obj.shader in shaders_index:
                i = shaders_index.index(obj.shader)
                groups[i][1].append(obj)
            else:
                shaders_index.append(obj.shader)
                groups.append((obj.shader, [obj]))

        self.shader_objects_sorted = True
        self.shader_objects = groups

        return groups

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
        rc = self.render_cache
        width, height = self.engine.info["swapchain_extent"].values()
        viewport = hvk.viewport(width=width, height=height)
        scissor = hvk.rect_2d(0, 0, width, height)

        render_pass_begin = hvk.render_pass_begin_info(
            render_pass = self.engine.render_target.render_pass,
            framebuffer = 0,
            render_area = hvk.rect_2d(0, 0, 0, 0),
            clear_values = (
                hvk.clear_value(color=(0.1, 0.1, 0.1, 1.0)),
                hvk.clear_value(depth=1.0, stencil=0)
            )
        )

        rc["begin_info"] = hvk.command_buffer_begin_info()
        rc["viewports"] = (viewport,)
        rc["scissors"] = (scissor,)
        rc["render_pass_begin_info"] = render_pass_begin
        rc["render_area_extent"] = render_pass_begin.render_area.extent

    #
    # Update things
    #

    def _update_uniforms(self, objects, shaders):
        mem = self.engine.memory_manager
        uniforms_alloc = self.uniforms_alloc
        base_offset = map_size = None
        update_list = []

        def process_uniforms(items):
            for x, y in items:
                uniforms = x.uniforms
                for name in uniforms.updated_member_names:
                    read_offets(uniforms, y, name)
                uniforms.updated_member_names.clear()

        def read_offets(uniforms, dobj, name):
            nonlocal update_list, base_offset, map_size

            offset, size = dobj.write_sets_update_infos[name]
            offset_size = offset + size

            if base_offset is None or offset < base_offset:
                base_offset = offset 

            if map_size is None or offset_size > map_size:
                map_size = size

            update_list.append( (getattr(uniforms, name), offset) )

        process_uniforms(objects)
        process_uniforms(shaders)

        with mem.map_alloc(uniforms_alloc, base_offset, map_size) as mapping:
            for value, offset in update_list:
                mapping.write_typed_data(value, offset-base_offset)
