from vulkan import vk, helpers as hvk
from .data_shader import DataShader
from .data_compute import DataCompute
from .data_mesh import DataMesh
from .data_sampler import DataSampler
from .data_image import DataImage
from .data_game_object import DataGameObject
from ..base_types import UniformsMaps
from ..public_components import GameObject, Shader, Compute
from ctypes import sizeof, memset


class DataScene(object):

    def __init__(self, engine, scene):
        self.engine = engine
        self.scene = scene

        self.command_pool = None
        self.render_commands = None
        self.compute_pools = None
        self.compute_commands = None
        self.render_cache = {}

        self.shaders = None
        self.computes = None
        self.objects = None

        self.pipelines = None
        self.compute_pipelines = None
        self.pipeline_cache = None

        self.descriptor_pool = None

        self.shader_objects = None
        self.shader_objects_sorted = False

        self.meshes_alloc = None
        self.meshes_buffer = None
        self.meshes = None

        self.samplers = None

        self.images_alloc = None
        self.images = None

        self.uniforms_alloc = None
        self.uniforms_buffer = None

        self._setup_shaders()
        self._setup_objects()
        self._setup_uniforms()
        self._setup_pipelines()
        self._setup_compute_pipelines()
        self._setup_descriptor_sets_pool()
        self._setup_descriptor_sets()
        self._setup_descriptor_write_sets()
        self._setup_render_commands()
        self._setup_compute_commands()
        self._setup_render_cache()

    def free(self):
        engine, api, device = self.ctx
        mem = engine.memory_manager

        if self.uniforms_alloc is not None:
            hvk.destroy_buffer(api, device, self.uniforms_buffer)
            mem.free_alloc(self.uniforms_alloc)

        if self.descriptor_pool is not None:
            hvk.destroy_descriptor_pool(api, device, self.descriptor_pool)

        for pipeline in self.pipelines:
            hvk.destroy_pipeline(api, device, pipeline)
        
        for pipeline in self.compute_pipelines:
            hvk.destroy_pipeline(api, device, pipeline)

        hvk.destroy_pipeline_cache(api, device, self.pipeline_cache)

        if self.meshes_buffer is not None:
            hvk.destroy_buffer(api, device, self.meshes_buffer)
            mem.free_alloc(self.meshes_alloc)

        for sampler in self.samplers:
            sampler.free()

        for img in self.images:
            for view in img.views.values():
                hvk.destroy_image_view(api, device, view)

            img.free()

        if self.images_alloc is not None:
            mem.free_alloc(self.images_alloc)

        for compute in self.computes:
            compute.free()

        for shader in self.shaders:
            shader.free()

        hvk.destroy_command_pool(api, device, self.command_pool)

        for _, pool in self.compute_pools:
            hvk.destroy_command_pool(api, device, pool)

        # Make it easier for python to deal with the circular dependencies
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

        for data_obj in self.objects:
            obj = data_obj.obj

            if data_obj.pipeline is not None and pipeline_index != data_obj.pipeline:
                pipeline_index = data_obj.pipeline
                hvk.bind_pipeline(api, cmd, pipelines[pipeline_index], vk.PIPELINE_BIND_POINT_GRAPHICS)
                hvk.set_viewport(api, cmd, viewports)
                hvk.set_scissor(api, cmd, scissors)

            if data_obj.shader is not None and current_shader_index != data_obj.shader:
                current_shader_index = data_obj.shader
                current_shader = shaders[data_obj.shader]

                if len(current_shader.descriptor_sets) > 0:
                    hvk.bind_descriptor_sets(api, cmd, vk.PIPELINE_BIND_POINT_GRAPHICS, current_shader.pipeline_layout, current_shader.descriptor_sets)

            if data_obj.descriptor_sets is not None and len(data_obj.descriptor_sets) > 0:
                hvk.bind_descriptor_sets(api, cmd, vk.PIPELINE_BIND_POINT_GRAPHICS, current_shader.pipeline_layout, data_obj.descriptor_sets, firstSet=len(current_shader.descriptor_sets))

            if data_obj.mesh is not None and not obj.hidden:
                mesh = meshes[data_obj.mesh]
                shader = shaders[data_obj.shader]

                attributes_buffer = [meshes_buffer] * len(mesh.attribute_offsets)
                attribute_offsets = mesh.attribute_offsets_for_shader(shader)

                h.bind_index_buffer(api, cmd, meshes_buffer, mesh.indices_offset, mesh.indices_type)
                h.bind_vertex_buffers(api, cmd, attributes_buffer, attribute_offsets)

                h.draw_indexed(api, cmd, mesh.indices_count)

        h.end_render_pass(api, cmd)
        h.end_command_buffer(api, cmd)

    def apply_updates(self):
        scene = self.scene
        obj_update, shader_update = [], []

        for obj in scene.update_obj_set:
            t, data_objs = type(obj), None
            if t is GameObject:
                data_objs = self.objects
            else:
                raise RuntimeError(f"Unkown object type {t.__qualname__} in object update list")

            if len(obj.uniforms.updated_member_names) > 0:
                dobj = data_objs[obj.id]
                obj_update.append((obj, dobj))

        for shader in scene.update_shader_set:
            t, data_objs = type(shader), None
            if t is Compute:
                data_objs = self.computes
            elif t is Shader:
                data_objs = self.shaders
            else:
                raise RuntimeError(f"Unkown object type {t.__qualname__} in shader update list")

            if len(shader.uniforms.updated_member_names) > 0:
                dshader = data_objs[shader.id]
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

        computes = []
        for compute in self.scene.computes:
            computes.append(DataCompute(e, compute))

        self.computes = computes
        self.shaders = shaders

    def _setup_objects(self):
        engine, api, device = self.ctx
        mem = engine.memory_manager

        scene = self.scene
        meshes = scene.meshes
        images = scene.images

        staging_mesh_offset = 0
        data_meshes, data_objects, data_images, data_samplers = [], [], [], []

        # Objects setup
        for obj in scene.objects:
            data_objects.append(DataGameObject(obj))

        # Samplers
        for sampler in scene.samplers:
            data_samplers.append(DataSampler(engine, sampler))

        # Meshes setup
        for mesh in meshes:
            data_mesh = DataMesh(mesh, staging_mesh_offset)
            data_meshes.append(data_mesh)
            staging_mesh_offset += mesh.size()

        # Images
        staging_image_offset = (staging_mesh_offset + 256) & ~255   # staging_image_offset must be aligned to 256 bits for uploading purpose

        for image in images:
            data_image = DataImage(engine, image, staging_image_offset)
            data_images.append(data_image)

            # Make sure that the image aligment is 16 bits or else the uploading of certain type of compressed image will fail
            # This could be impoved by checking the image format aligment requirement instead
            img_size = image.size()
            if img_size % 16 != 0:
                staging_image_offset += (img_size + 16) & ~15
            else:
                staging_image_offset += img_size

        if len(meshes) == 0 and len(images) == 0:
            staging_alloc = staging_buffer = meshes_alloc = meshes_buffer = images_alloc = None
        else:
            staging_alloc, staging_buffer = self._setup_objects_staging(staging_image_offset, data_meshes, data_images)
            meshes_alloc = meshes_buffer = images_alloc = None
            if len(meshes) > 0:
                meshes_alloc, meshes_buffer = self._setup_meshes_resources(staging_alloc, staging_buffer, staging_mesh_offset)
            if len(images) > 0:
                images_alloc = self._setup_images_resources(staging_alloc, staging_buffer, data_images)

        self.meshes_alloc = meshes_alloc
        self.meshes_buffer = meshes_buffer
        self.meshes = data_meshes
        self.images_alloc = images_alloc
        self.images = data_images
        self.samplers = data_samplers
        self.objects = data_objects

        if staging_buffer is not None:
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
                alloc.write_bytes(di.base_staging_offset, di.as_ctypes_array())
  
        return staging_alloc, staging_buffer

    def _setup_meshes_resources(self, staging_alloc, staging_buffer, mesh_buffer_size):
        engine, api, device = self.ctx
        mem = engine.memory_manager
        cmd = engine.setup_command_buffer

        # Final buffer allocation
        mesh_buffer = hvk.create_buffer(api, device, hvk.buffer_create_info(
            size = mesh_buffer_size, 
            usage = vk.BUFFER_USAGE_INDEX_BUFFER_BIT | vk.BUFFER_USAGE_VERTEX_BUFFER_BIT | vk.BUFFER_USAGE_TRANSFER_DST_BIT
        ))
        mesh_alloc = mem.alloc(mesh_buffer, vk.STRUCTURE_TYPE_BUFFER_CREATE_INFO, (vk.MEMORY_PROPERTY_DEVICE_LOCAL_BIT,))

        # Uploading commands
        region = vk.BufferCopy(src_offset=0, dst_offset=0, size=mesh_buffer_size)
        regions = (region,)

        hvk.begin_command_buffer(api, cmd, hvk.command_buffer_begin_info())
        hvk.copy_buffer(api, cmd, staging_buffer, mesh_buffer, regions)
        hvk.end_command_buffer(api, cmd)

        # Submitting
        engine.submit_setup_command(wait=True)

        return mesh_alloc, mesh_buffer

    def _setup_images_resources(self, staging_alloc, staging_buffer, data_images):
        engine, api, device = self.ctx
        mem = engine.memory_manager

        # Allocate final images memory 

        total_images_alloc = 0

        for data_image in data_images:
            req = hvk.image_memory_requirements(api, device, data_image.image_handle)
            
            a, o = req.alignment-1, total_images_alloc
            aligned = (o + a) & ~a

            data_image.base_offset = aligned
            total_images_alloc = aligned + req.size

        image_alloc = mem.shared_alloc(total_images_alloc, (vk.MEMORY_PROPERTY_DEVICE_LOCAL_BIT,))

        # Bind image to memory & create image views
        for data_image in data_images:
            image_handle = data_image.image_handle
            hvk.bind_image_memory(api, device, image_handle, image_alloc.device_memory, data_image.base_offset)
            data_image._setup_views()
            
        # Update the image layouts to match the requested parameters
        self._setup_image_layouts(staging_buffer, data_images)

        return image_alloc

    def _setup_image_layouts(self, staging_buffer, data_images):
        engine, api, device = self.ctx

        to_transfer = hvk.image_memory_barrier(
            image = 0,
            new_layout = vk.IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            dst_access_mask = vk.ACCESS_TRANSFER_WRITE_BIT,
            subresource_range = hvk.image_subresource_range(
                level_count = 0
            )
        )

        to_final_layout = hvk.image_memory_barrier(
            image = 0,
            old_layout = vk.IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            new_layout = 0,
            src_access_mask = vk.ACCESS_TRANSFER_WRITE_BIT,
            dst_access_mask = 0,
            subresource_range = hvk.image_subresource_range(
                level_count = 0
            )
        )

        cmd = engine.setup_command_buffer
        hvk.begin_command_buffer(api, cmd, hvk.command_buffer_begin_info())

        for data_image in data_images:
            image = data_image.image
            image_handle = data_image.image_handle
            regions = []

            for m in image.iter_mipmaps():
                if (data_image.base_staging_offset + m.offset) % 16 != 0:
                    msg1 = f"Buffer offet aligment, when copying image data, must by 16. Got {(data_image.base_staging_offset + m.offset)}"
                    msg2 = msg1 + f", reminder {(data_image.base_staging_offset + m.offset) % 16}"
                    raise ValueError(msg2)

                r = hvk.buffer_image_copy(
                    image_subresource = hvk.image_subresource_layers( mip_level = m.level, base_array_layer = m.layer ),
                    image_extent = vk.Extent3D(m.width, m.height, 1),
                    buffer_offset =  data_image.base_staging_offset + m.offset
                )
                regions.append(r)

            to_transfer.image = image_handle
            to_transfer.subresource_range.level_count = image.mipmaps_levels
            to_transfer.subresource_range.layer_count = image.array_layers

            to_final_layout.image = image_handle
            to_final_layout.new_layout = data_image.target_layout
            to_final_layout.dst_access_mask = data_image.target_access_mask
            to_final_layout.subresource_range.level_count = image.mipmaps_levels
            to_final_layout.subresource_range.layer_count = image.array_layers
            
            hvk.pipeline_barrier(api, cmd, (to_transfer,), dst_stage_mask=vk.PIPELINE_STAGE_TRANSFER_BIT)
            hvk.copy_buffer_to_image(api, cmd, staging_buffer, image_handle, vk.IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, regions)
            hvk.pipeline_barrier(api, cmd, (to_final_layout,), dst_stage_mask=hvk.dst_stage_mask_for_access_mask(to_final_layout.dst_access_mask))

        hvk.end_command_buffer(api, cmd)

        # Sumbit the images and update the layer values in the images
        engine.submit_setup_command(wait=True)
        for img in data_images:
            img.layout = img.target_layout
            img.access_mask = img.target_access_mask

    def _setup_uniforms(self):
        scene = self.scene
        data_shaders, data_computes = self.shaders, self.computes
        
        filters_names = UniformsMaps._NON_UNIFORM_NAMES

        def map_layouts(obj, layouts):
            uniforms = obj.uniforms
            uniforms_members = [f for f in dir(uniforms) if f[0] != "_" and f not in filters_names]
            
            for layout in layouts:
                # Image based uniforms are specified in `images`
                for name in layout.images:
                    default = getattr(uniforms, name, None)
                    if default is None:
                        msg = f"Default for sampler based uniforms is not yet implemented. To fix this set a default value to uniform \"{name}\" of component \"{obj.name}\""
                        raise NotImplementedError(msg)
                    else:
                        uniforms_members.remove(name)

                    uniforms.uniform_names.append(name)

                # Buffer based uniforms are specified in `struct_map`
                for name, struct in layout.struct_map.items():
                    default = getattr(uniforms, name, None)
                    if default is not None:
                        value = struct(**default)
                        uniforms_members.remove(name)
                        uniforms.updated_member_names.add(name)
                    else:
                        value = struct()

                    setattr(uniforms, name, value)
                    uniforms.uniform_names.append(name)

            if len(uniforms_members) != 0:
                print(f"WARNING: uniforms for object {obj.name} contains member(s) that do not map with the associated shader: {uniforms_members}")

        # Shaders global uniforms
        for shader, data_shader in zip(scene.shaders, data_shaders):
            map_layouts(shader, data_shader.global_layouts)
            shader.uniforms.bound = True

        # Compute shaders global uniforms
        for compute, data_compute in zip(scene.computes, data_computes):
            map_layouts(compute, data_compute.global_layouts)
            compute.uniforms.bound = True

        # Objects local uniforms
        for obj in scene.objects:
            if obj.shader is not None:
                data_shader = data_shaders[obj.shader]
                map_layouts(obj, data_shader.local_layouts)

            obj.uniforms.bound = True

    def _setup_pipelines(self):
        engine, api, device = self.ctx
        shaders = self.shaders
        rt = engine.render_target
        
        assembly = hvk.pipeline_input_assembly_state_create_info()
        multisample = hvk.pipeline_multisample_state_create_info()
        viewport = hvk.pipeline_viewport_state_create_info(viewport_count=1, scissor_count=1)
        raster = hvk.pipeline_rasterization_state_create_info()
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

        # Create the pipeline from the scene shaders
        pipeline_infos = []
        for data_shader in shaders:
            info = hvk.graphics_pipeline_create_info(
                stages = data_shader.stage_infos,
                vertex_input_state = data_shader.vertex_input_state,
                input_assembly_state = assembly,
                viewport_state = viewport,
                rasterization_state = raster,
                multisample_state = multisample,
                depth_stencil_state = depth_stencil,
                color_blend_state = color_blend,
                dynamic_state = dynamic_state,
                layout = data_shader.pipeline_layout,
                render_pass = rt.render_pass
            )

            pipeline_infos.append(info)
            
        # Associate the pipelines with the objets
        for shader_index, objects in self._group_objects_by_shaders():
            for obj in objects:
                obj.pipeline = shader_index

        self.pipeline_cache = hvk.create_pipeline_cache(api, device, hvk.pipeline_cache_create_info())

        if len(pipeline_infos) > 0:
            self.pipelines = hvk.create_graphics_pipelines(api, device, pipeline_infos, self.pipeline_cache)
        else:
            self.pipelines = []

    def _setup_compute_pipelines(self):
        engine, api, device = self.ctx

        pipeline_infos = []
        for compute_index, data_compute in enumerate(self.computes):
            data_compute.pipeline = compute_index
            
            info = hvk.compute_pipeline_create_info(
                flags = 0,
                stage = data_compute.module_stage,
                layout = data_compute.pipeline_layout
            )

            pipeline_infos.append(info)

        if len(pipeline_infos) > 0:
            self.compute_pipelines = hvk.create_compute_pipelines(api, device, pipeline_infos, self.pipeline_cache)
        else:
            self.compute_pipelines = []

    def _setup_descriptor_sets_pool(self):
        _, api, device = self.ctx
        shaders, computes = self.shaders, self.computes

        pool_sizes, max_sets = {}, 0

        # Lookup for the shader global descriptors
        for data_shader in shaders:
            if data_shader.descriptor_set_layouts is None:
                continue

            for dset_layout in data_shader.global_layouts:
                for dtype, dcount in dset_layout.pool_size_counts:
                    if dtype in pool_sizes:
                        pool_sizes[dtype] += dcount
                    else:
                        pool_sizes[dtype] = dcount
            
                max_sets += 1

        # Lookup for the compute shader global descriptor
        for data_compute in computes:
            if data_compute.descriptor_set_layouts is None:
                continue

            for dset_layout in data_compute.global_layouts:
                for dtype, dcount in dset_layout.pool_size_counts:
                    if dtype in pool_sizes:
                        pool_sizes[dtype] += dcount
                    else:
                        pool_sizes[dtype] = dcount
            
                max_sets += 1

        # Lookup for the object local descriptors
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

        if len(pool_sizes) == 0:
            self.descriptor_pool = None
            return

        pool_sizes = tuple( vk.DescriptorPoolSize(type=t, descriptor_count=c) for t, c in pool_sizes.items() )
        pool = hvk.create_descriptor_pool(api, device, hvk.descriptor_pool_create_info(
            max_sets = max_sets,
            pool_sizes = pool_sizes
        ))

        self.descriptor_pool = pool

    def _setup_descriptor_sets(self):
        engine, api, device = self.ctx
        shaders, computes = self.shaders, self.computes
        descriptor_pool = self.descriptor_pool
        mem = engine.memory_manager
       
        uniforms_buffer_size = 0

        # Allocate shader global descriptor sets
        for data_shader in shaders:
            uniforms_buffer_size += sum( l.struct_map_size_bytes for l in data_shader.global_layouts )
            set_layouts_global = [ l.set_layout for l in data_shader.global_layouts ]

            if len(set_layouts_global) == 0:
                data_shader.descriptor_sets = []
                continue

            descriptor_sets = hvk.allocate_descriptor_sets(api, device, hvk.descriptor_set_allocate_info(
                descriptor_pool = descriptor_pool,
                set_layouts = set_layouts_global
            ))

            data_shader.descriptor_sets = descriptor_sets

        # Allocate compute shader global descriptor sets
        for data_compute in computes:
            uniforms_buffer_size += sum( l.struct_map_size_bytes for l in data_compute.global_layouts )
            set_layouts_global = [ l.set_layout for l in data_compute.global_layouts ]

            if len(set_layouts_global) == 0:
                data_compute.descriptor_sets = []
                continue

            descriptor_sets = hvk.allocate_descriptor_sets(api, device, hvk.descriptor_set_allocate_info(
                descriptor_pool = descriptor_pool,
                set_layouts = set_layouts_global
            ))

            data_compute.descriptor_sets = descriptor_sets

        # Allocate object local descriptor sets
        for shader_index, objects in self._group_objects_by_shaders():
            shader = shaders[shader_index]
            objlen = len(objects)
            
            # Uniforms buffer size
            uniforms_buffer_size += sum( l.struct_map_size_bytes for l in shader.local_layouts ) * objlen
            
            # Descriptor sets allocations
            set_layouts_local = [ l.set_layout for l in shader.local_layouts ] * objlen
            if len(set_layouts_local) == 0:
                for obj in objects:
                    obj.descriptor_sets = []
                continue

            descriptor_sets = hvk.allocate_descriptor_sets(api, device, hvk.descriptor_set_allocate_info(
                descriptor_pool = descriptor_pool,
                set_layouts = set_layouts_local
            ))

            # Save the local layouts to the objects
            step = len(tuple(shader.local_layouts))
            if step == 0:
                continue
                
            end = len(descriptor_sets)
            iter_objects = iter(objects)
            for i in range(0, end, step):
                obj = next(iter_objects)
                obj.descriptor_sets = descriptor_sets[i:i+step]

        # Uniform buffer creation
        if uniforms_buffer_size == 0:
            self.uniforms_alloc = self.uniforms_buffer = None
            return

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
        shaders, computes, data_samplers, data_images = self.shaders, self.computes, self.samplers, self.images
        uniform_buffer = self.uniforms_buffer
        uniform_offset = 0
        
        write_sets_to_update = []

        def generate_write_set(obj, wst, descriptor_set):
            nonlocal uniform_buffer, uniform_offset
            name, dtype, drange, binding = wst['name'], wst['descriptor_type'], wst['range'], wst['binding']

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

            elif dtype in (vk.DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, vk.DESCRIPTOR_TYPE_STORAGE_IMAGE):
                image_id, view_name, sampler_id = getattr(obj.uniforms, name)

                data_image = data_images[image_id]
                data_sampler = data_samplers[sampler_id]
                data_view = data_image.views.get(view_name, None)

                if data_view is None:
                    raise ValueError(f"No view named \"{view_name}\" for image \"{data_image.image.name}\"")

                image_info = vk.DescriptorImageInfo(
                    sampler = data_sampler.sampler_handle,
                    image_view = data_view,
                    image_layout = data_image.layout
                )

                write_set = hvk.write_descriptor_set(
                    dst_set = descriptor_set,
                    dst_binding = binding,
                    descriptor_type = dtype,
                    image_info = (image_info,)
                )

                # Clear the accessed uniforms names for images because we don't actually need to mark them as updated
                obj.uniforms.updated_member_names.remove(name)

            else:
                raise ValueError(f"Unknown descriptor type: {dtype}")

            return write_set

        def map_write_sets(data_obj, obj, layouts):
            write_sets = {}

            for descriptor_set, descriptor_layout in zip(data_obj.descriptor_sets, layouts):
                for wst in descriptor_layout.write_set_templates:
                    name = wst["name"]
                    buffer_offset_range = None

                    if wst["buffer"]:
                        buffer_offset_range = (uniform_offset, wst["range"])

                    write_set = generate_write_set(obj, wst, descriptor_set)
                    write_sets_to_update.append(write_set)
                    write_sets[name] = {
                        "buffer_offset_range": buffer_offset_range,
                        "write_set": write_set
                    }

            return write_sets

        for data_shader in shaders:
            data_shader.write_sets = map_write_sets(data_shader, data_shader.shader, data_shader.global_layouts)

        for data_compute in computes:
            data_compute.write_sets = map_write_sets(data_compute, data_compute.compute, data_compute.global_layouts)

        for shader_index, objects in self._group_objects_by_shaders():
            data_shader = shaders[shader_index]

            # Local descriptor sets
            for data_obj in objects:
                data_obj.write_sets = map_write_sets(data_obj, data_obj.obj, data_shader.local_layouts)

        hvk.update_descriptor_sets(api, device, write_sets_to_update, ())

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

    def _setup_compute_commands(self):
        engine, api, device = self.ctx
        compute_shaders = self.computes

        pool_create_info = hvk.command_pool_create_info(
            queue_family_index = 0,
            flags = vk.COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT
        )

        allocate_info = hvk.command_buffer_allocate_info(
            command_pool = 0,
            command_buffer_count = 0,
            level = vk.COMMAND_BUFFER_LEVEL_PRIMARY
        )
        
        # Count the number of compute command buffers that will be allocated per queue
        queues = tuple(engine.queues.values())
        command_buffers_per_queues = [0 for q in queues]
        for index, queue in enumerate(queues):
            count = sum(1 for c in compute_shaders if c.queue is queue)
            command_buffers_per_queues[index] += count

        # Allocate a single command pool for every queue with at least 1 command buffer
        queue_pool_count = []
        for index, count in enumerate(command_buffers_per_queues):
            if count == 0:
                continue

            queue = queues[index]
            pool_create_info.queue_family_index = queue.family.index
            pool = hvk.create_command_pool(api, device, pool_create_info)
            queue_pool_count.append( (queue, pool, count) )

        # Allocate the commands buffers and link them with the compute process
        command_index = 0
        command_buffers = []
        for queue, pool, count in queue_pool_count:
            for c in compute_shaders:
                if c.queue != queue:
                    continue

                c.command_index = command_index
                command_index += 1

            allocate_info.command_pool = pool
            allocate_info.command_buffer_count = count
            buffers = hvk.allocate_command_buffers(api, device, allocate_info)
            command_buffers.extend(buffers)

        self.compute_pools = tuple( (q, p) for q, p, _ in queue_pool_count )
        self.compute_commands = command_buffers

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
                hvk.clear_value(color=(0.15, 0.15, 0.15, 1.0)),
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
        uniforms_alloc = self.uniforms_alloc
        base_offset = map_size = None
        buffer_update_list = []
        
        data_samplers, data_images = self.samplers, self.images
        image_write_sets = []

        def read_buffer_offets(uniforms, dobj, obj, uniform_name):
            nonlocal buffer_update_list, base_offset, map_size

            # Skips image uniforms
            buffer_offset_range = dobj.write_sets[uniform_name]["buffer_offset_range"]
            if buffer_offset_range is None:
                return

            # Fetch the new uniform value
            buffer_value = getattr(uniforms, uniform_name)

            # Update the mapping info from the size and offset of the uniforms value
            offset, size = buffer_offset_range
            offset_size = offset+size
            if base_offset is None or offset < base_offset:
                base_offset = offset 

            if map_size is None or offset_size > map_size:
                map_size = size

            buffer_update_list.append( (buffer_value, offset) )

        def read_image_write_sets(uniforms, dobj, obj, uniform_name):
            nonlocal image_write_sets, data_images, data_samplers

            write_set_info = dobj.write_sets[uniform_name]
            if write_set_info["buffer_offset_range"] is not None:
                return

            # Fetch the new image CombinedSampler value
            image_sampler = getattr(uniforms, uniform_name)
            data_sampler = data_samplers[image_sampler.sampler_id]
            data_image = data_images[image_sampler.image_id]
            data_view = data_image.views.get(image_sampler.view_name, None)

            if data_view is None:
                raise ValueError(f"No view named \"{view_name}\" for image \"{data_image.image.name}\" of component {obj.name}")

            # Fetch the write set associated with the updated uniform value
            write_set = write_set_info["write_set"]
            
            # Update the image info
            image_info = write_set.image_info[0]
            image_info.sampler = data_sampler.sampler_handle
            image_info.image_layout = data_image.layout
            image_info.image_view = data_view

            image_write_sets.append(write_set)
            
        def process_uniforms(items):
            for obj, data_obj in items:
                uniforms = obj.uniforms
                for uniform_name in uniforms.updated_member_names:
                    # Find the offsets in the uniforms buffer for the updated buffer uniforms
                    read_buffer_offets(uniforms, data_obj, obj, uniform_name)

                    # Fetch the write sets for the updated image uniforms
                    read_image_write_sets(uniforms, data_obj, obj, uniform_name)
                
                uniforms.updated_member_names.clear()

        process_uniforms(objects)
        process_uniforms(shaders)

        # Update the image uniforms
        _, api, device = self.ctx
        hvk.update_descriptor_sets(api, device, image_write_sets, ())

        # Update the uniform buffers
        mem = self.engine.memory_manager
        with mem.map_alloc(uniforms_alloc, base_offset, map_size) as mapping:
            for value, offset in buffer_update_list:
                mapping.write_typed_data(value, offset-base_offset)
