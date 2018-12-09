from PyQt5.QtWidgets import (QApplication, QWidget, QTabWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QComboBox, QGridLayout,
 QTableWidget, QTableWidgetItem, QAbstractItemView, QLabel, QFrame, QPushButton, QHBoxLayout, QLineEdit, QSizePolicy, QShortcut )
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QKeySequence
from functools import lru_cache
from multiprocessing import Process, JoinableQueue, Queue
from collections import namedtuple
from queue import Empty


DataPair = namedtuple("DataPair", ("name", "children"))
DataItem = namedtuple("DataItem", ("name", "children", "attributes"))


class DebugUI(object):

    def __init__(self, engine):
        self.engine = engine
        self._sync = False
        self.send_queue = q = JoinableQueue()
        self.recv_queue = q2 = Queue()
        self.process = process = Process(target=DebugUIProcess, args=(q, q2))
        self.events_dispatch = {
            "update_uniform": self._update_uniform
        }

        process.start()

    @property
    def sync(self):
        self._sync = True
        return self

    def events(self):
        try:
            while True:
                message = self.recv_queue.get_nowait()
                dispatch = self.events_dispatch[message["action"]]
                dispatch(message)
        except Empty:
            pass

    def load_scene(self, data_scene):
        objects, shaders, meshes, images, samplers = [], [], [], [], []
        base_scene = data_scene.scene

        for data_obj in data_scene.objects:
            obj = data_obj.obj
            serialized_obj = DataItem(obj.name, (), { "id": id(obj), "uniforms": obj.uniforms.as_dict() })
            objects.append(serialized_obj)

        for data_shader in data_scene.shaders:
            shader = data_shader.shader
            serialized_shader = DataItem(shader.name, (), { "id": id(shader), "uniforms": shader.uniforms.as_dict() })
            shaders.append(serialized_shader)

        for data_mesh in data_scene.meshes:
            mesh = data_mesh.mesh
            serialized_mesh = DataItem(mesh.name, (), { "id": id(mesh), })
            meshes.append(serialized_mesh)

        for data_image in data_scene.images:
            image = data_image.image
            serialized_image = DataItem(image.name, (), { "id": id(image), })
            images.append(serialized_image)

        for data_sampler in data_scene.samplers:
            sampler = data_sampler.sampler
            serialized_sampler = DataItem(sampler.name, (), { "id": id(sampler), })
            samplers.append(serialized_sampler)

        serialized_scene = (
            DataPair("Objects", objects),
            DataPair("Shaders", shaders),
            DataPair("Meshes", meshes),
            DataPair("Images", images),
            DataPair("Samplers", samplers)
        )
        self.sync_scene(serialized_scene)

    def _update_uniform(self, message):
        engine = self.engine
        scene_data = engine.graph[engine.current_scene_index]
        scene = scene_data.scene

        components = comset = None
        comtype = message["component_type"]
        if comtype == "object":
            components = scene.objects
            comset = scene.update_obj_set
        elif comtype == "shader":
            components = scene.shaders
            comset = scene.update_shader_set
        else:
            print(f"Invalid component type when updating uniform: {message}")
            return

        obj_id = message["id"]
        com = next((com for com in components if id(com) == obj_id), None)
        if com is None:
            print(f"Could not find component associated with message: {message}")
            return
        
        try:
            uni = getattr(com.uniforms, message["uniform"])
            field = getattr(uni, message["field"])
            field[::] = message["value"]
            comset.add(com)
        except Exception as e:
            print(f"Failed to associate new uniform value: {e}")

    @lru_cache(maxsize=None)
    def __getattr__(self, name):
        if name in dir(DebugUIProcess):

            def send(*args, **kwargs):
                if not self.process.is_alive():
                    print("ERROR: remote process was closed")
                    return

                self.send_queue.put((name, args, kwargs))
                if self._sync: 
                    self.send_queue.join()
                self._sync = False

            return send
        else:
            raise AttributeError(f"No function named {name} in remote process")


class DebugUIProcess(object):

    def __init__(self, recv_queue, send_queue):
        self.recv_queue = recv_queue
        self.send_queue = send_queue
        self.app = app = QApplication([])
        self.scene_data = None

        self.scene_tree = self.objects_form = self.shaders_form = self.meshes_form = None
        self.samplers_form = self.images_form = None
        self.current_object = self.current_shader = self.current_mesh = None
        self.current_image = self.current_sampler = None
        self.object_uniform_inspector = self.shader_uniform_inspector = None
        self.object_uniform_editor = self.shader_uniform_editor = None
        self.tabs = None

        self.window = QWidget()
        #self.window.closeEvent = lambda evt: evt.ignore()
        self._init_window()

        self.timer = t = QTimer()
        t.setInterval(200)
        t.timeout.connect(lambda: self._read_queue() )
        t.start()

        app.exec_()

    def sync_scene(self, scene_data):
        tree, co, cs, cm = self.scene_tree, self.current_object, self.current_shader, self.current_mesh
        ci, csm = self.current_image, self.current_sampler
        tree.clear(); co.clear(); cs.clear(); cm.clear()

        self.tabs.setCurrentIndex(0)

        def fill_tree(data):
            nonlocal parent

            for name, children, *data in data:
                old_parent = parent
                parent = QTreeWidgetItem(parent, [name])
                fill_tree(children)
                parent = old_parent

        parent = tree
        fill_tree(scene_data)

        objects, shaders, meshes, images, samplers = scene_data

        for obj_name, _, data in objects.children:
            co.addItem(obj_name, data)

        for shader_name, _, data in shaders.children:
            cs.addItem(shader_name, data)

        for mesh_name, _, data in meshes.children:
            cm.addItem(mesh_name, data)

        for image_name, _, data in images.children:
            ci.addItem(image_name, data)

        for sampler_name, _, data in samplers.children:
            csm.addItem(sampler_name, data)

        tree.expandAll()

        self.scene_data = scene_data

    def tab_changed(self, index):
        item_combo = uniforms = None

        if index == 0:
            return
        elif index == 1:
            item_combo = self.current_object
            uniforms = self.object_uniform_inspector
        elif index == 2:
            item_combo = self.current_shader
            uniforms = self.shader_uniform_inspector
        elif index == 3:
            item_combo = self.current_mesh
            uniforms = None
        elif index == 4:
            item_combo = self.current_image
            uniforms = None
        elif index == 5:
            item_combo = self.current_sampler
            uniforms = None
        else:
            print(f"Bad index {index}")
            return

        data = item_combo.currentData()

        if uniforms is not None and item_combo is not None:
            uniforms.load_uniforms(data["uniforms"])

    def component_changed(self, index):
        tab_index = self.tabs.currentIndex()
        self.tab_changed(tab_index)

    def goto_item(self, item, col):
        tabs = self.tabs
        parent = item.parent()
        if parent is None:
            return

        item_index = parent.indexOfChild(item)
        parent_text = parent.text(0)
        if parent_text == "Objects":
            self.current_object.setCurrentIndex(item_index)
            tabs.setCurrentIndex(1)
        elif parent_text == "Shaders":
            self.current_shader.setCurrentIndex(item_index)
            tabs.setCurrentIndex(2)
        elif parent_text == "Meshes":
            self.current_mesh.setCurrentIndex(item_index)
            tabs.setCurrentIndex(3)
        elif parent_text == "Images":
            self.current_image.setCurrentIndex(item_index)
            tabs.setCurrentIndex(4)
        elif parent_text == "Samplers":
            self.current_sampler.setCurrentIndex(item_index)
            tabs.setCurrentIndex(5)
        else:
            print(f"Error: unknown parent text {parent_text}")

    def edit_uniform(self, row, column):
        current_tab = self.tabs.currentIndex()
        uniforms = inspector = item_combo = None
        if current_tab == 1:
            uniforms = self.object_uniform_editor
            inspector = self.object_uniform_inspector
            item_combo = self.current_object
        elif current_tab == 2:
            uniforms = self.shader_uniform_editor
            inspector = self.shader_uniform_inspector
            item_combo = self.current_shader
        else:
            print("ERROR: Current tab do not have a uniforms editor")
            return

        if item_combo.count() == 0:
            return

        data = item_combo.currentData()
        objname = item_combo.currentText()

        name = inspector.item(row, 0).text()
        field = inspector.item(row, 1).text()
        value = data["uniforms"][name][field]
        uniforms.edit(data["id"], objname, name, field, value)

        uniforms.show()

    def update_uniform(self, obj_id, uniform, field, value):
        current_tab = self.tabs.currentIndex()
        objects = item_combo = inspect = comtype = None

        if current_tab == 1:
            objects = self.scene_data[0][1]
            item_combo = self.current_object
            inspect = self.object_uniform_inspector
            comtype = "object"
        elif current_tab == 2:
            objects = self.scene_data[1][1]
            item_combo = self.current_shader
            inspect = self.shader_uniform_inspector
            comtype = "shader"
        else:
            return

        current_index = item_combo.currentIndex()
        current_data = item_combo.currentData()
        if current_data["id"] != obj_id:
            # If the current item was changed, go fetch back the original item
            current_data, current_index = next(((data, i) for i, (_, _, data) in enumerate(objects) if data["id"] == obj_id), None)

        if current_data is None:
            print(f"Could not fetch current data when updating uniform {(uniform, field)}")
            return
        
        current_data["uniforms"][uniform][field] = value
        item_combo.setItemData(current_index, current_data)

        for row in range(inspect.rowCount()):
            uniform2, field2 = inspect.item(row, 0).text(), inspect.item(row, 1).text()
            if uniform2 == uniform and field2 == field:
                inspect.item(row, 2).setText(repr(value))
                break

        # Send the updated uniform to the game process
        event = {"action": "update_uniform", "component_type": comtype, "id": obj_id, "uniform": uniform, "field": field, "value": value}
        self.send_queue.put(event)

    def close(self):
        #del self.window.closeEvent
        self.window.close()

    def _read_queue(self):
        try:
            while True:
                queue = self.recv_queue
                name, argv, kwargs = queue.get_nowait()
                value = getattr(self, name)(*argv, **kwargs)
                queue.task_done()
        except Empty:
            pass

    def _init_window(self):
        w = self.window

        self.scene_tree = stree = QTreeWidget()
        stree.header().hide()
        stree.itemDoubleClicked.connect(self.goto_item)

        self.current_object = cobj = QComboBox()
        self.object_uniform_inspector = uni1 = UniformInspector()
        self.object_uniform_editor = ed1 = UniformEditor()
        self.objects_form = of = QWidget()
        of_layout = QGridLayout()
        cobj.currentIndexChanged.connect(self.component_changed)
        of_layout.addWidget(cobj, 0, 0)
        uni1.cellClicked.connect(self.edit_uniform)
        of_layout.addWidget(uni1, 1, 0)
        ed1.save_requested = self.update_uniform
        of_layout.addWidget(ed1, 2, 0)
        of.setLayout(of_layout)

        self.current_shader = cshader = QComboBox()
        self.shader_uniform_inspector = uni2 = UniformInspector()
        self.shader_uniform_editor = ed2 = UniformEditor()
        self.shaders_form = sf = QWidget()
        sf_layout = QGridLayout()
        cshader.currentIndexChanged.connect(self.component_changed)
        sf_layout.addWidget(cshader, 0, 0)
        uni2.cellClicked.connect(self.edit_uniform)
        sf_layout.addWidget(uni2, 1, 0)
        ed2.save_requested = self.update_uniform
        sf_layout.addWidget(ed2, 2, 0)
        sf.setLayout(sf_layout)

        self.current_mesh = cmesh = QComboBox()
        self.meshes_form = mf = QWidget()
        mf_layout = QGridLayout()
        mf_layout.addWidget(cmesh, 0, 0)
        mf_layout.addWidget(QWidget(), 1, 0)
        mf.setLayout(mf_layout)

        self.current_image = cimg = QComboBox()
        self.images_form = imf = QWidget()
        imf_layout = QGridLayout()
        imf_layout.addWidget(cimg, 0, 0)
        imf_layout.addWidget(QWidget(), 1, 0)
        imf.setLayout(imf_layout)

        self.current_sampler = csamp = QComboBox()
        self.samplers_form = spf = QWidget()
        spf_layout = QGridLayout()
        spf_layout.addWidget(csamp, 0, 0)
        spf_layout.addWidget(QWidget(), 1, 0)
        spf.setLayout(spf_layout)

        self.tabs = tab = QTabWidget(w)
        tab.addTab(stree, "Scene")
        tab.addTab(of, "Objects")
        tab.addTab(sf, "Shaders")
        tab.addTab(mf, "Meshes")
        tab.addTab(imf, "Images")
        tab.addTab(spf, "Samplers")
        tab.currentChanged.connect(self.tab_changed)

        l = QVBoxLayout()
        l.addWidget(tab)

        w.setAttribute(Qt.WA_ShowWithoutActivating)
        w.setLayout(l)
        w.resize(450, 600)
        w.move(100, 250)
        w.setWindowTitle('Debug')
        w.show()


class UniformInspector(QTableWidget):

    def __init__(self):
        super().__init__()
        self.setColumnCount(3)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        header = self.horizontalHeader()
        header.setStretchLastSection(True)

        header = self.verticalHeader()
        header.hide()

    def load_uniforms(self, uniforms):
        self.clear()
        self.set_rows(uniforms)
        self.setHorizontalHeaderLabels(("Uniform", "Member", "Value"))

        count = 0
        for name, fields in uniforms.items():
            for fname, value in fields.items():
                self.setItem(count, 0, QTableWidgetItem(name))
                self.setItem(count, 1, QTableWidgetItem(fname))
                self.setItem(count, 2, QTableWidgetItem(repr([round(x, 4) for x in value])))
                count += 1

    def set_rows(self, uniforms):
        count = 0
        for name, fields in uniforms.items():
            count += len(fields)
        
        self.setRowCount(count)


class UniformEditor(QFrame):

    def __init__(self):
        super().__init__()
        
        self.object = None
        self.uname = None
        self.ufield = None
        self.uvalue = None
        self.old_uvalue = None

        self.save_requested = lambda a, b, c, d: None

        self.uniform_name = QLabel()
        self.error_label = el = QLabel()
        el.hide()

        self.value_edit = ve = QLineEdit()
        ve.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.save_shortcut = ss = QShortcut(QKeySequence(Qt.Key_Return), self.value_edit)
        ss.activated.connect(self.save)

        hide_btn = QPushButton("Hide")
        hide_btn.clicked.connect(self.hide)

        sync_btn = QPushButton("Reload")
        sync_btn.clicked.connect(self.reload)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(hide_btn)
        btn_layout.addWidget(sync_btn)
        btn_layout.addWidget(save_btn)

        l = QVBoxLayout()
        l.addWidget(self.uniform_name)
        l.addWidget(self.value_edit)
        l.addWidget(self.error_label)
        l.addLayout(btn_layout)
    
        self.setFrameShape(QFrame.Box)
        self.setLayout(l)
        self.hide()

    def edit(self, obj_id, objname, name, field, value):
        self.obj_id = obj_id
        self.uname = name
        self.ufield = field
        self.uvalue = value
        self.old_uvalue = value

        self.uniform_name.setText(f"Uniform \"{name}.{field}\" for \"{objname}\"")
        self.value_edit.setText(repr([round(x, 4) for x in value]))

    def reload(self):
        self.value_edit.setText(repr(self.old_uvalue))
        self.uvalue = self.old_uvalue

    def save(self):
        try:
            v = eval(self.value_edit.text())
            if not isinstance(v, (list, tuple)):
                self.error_label.setText(f"Error: value must be an array got \"{v}\"")
                return 

            self.uvalue = v
            self.old_uvalue = self.uvalue
            self.error_label.hide()

            self.save_requested(self.obj_id, self.uname, self.ufield, v)
        except Exception as e:
            self.error_label.setText(f"Error: {repr(e)}")
            self.error_label.show()
