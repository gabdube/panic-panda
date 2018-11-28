from multiprocessing import Process, JoinableQueue
from queue import Empty
from PyQt5.QtWidgets import (QApplication, QWidget, QTabWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QComboBox, QGridLayout,
 QTableWidget, QTableWidgetItem, QAbstractItemView, QLabel, QFrame)
from PyQt5.QtCore import QTimer, Qt
from functools import lru_cache


class DebugUI(object):

    def __init__(self, engine):
        self.engine = engine
        self._sync = False
        self.queue = q = JoinableQueue()
        self.process = process = Process(target=DebugUIProcess, args=(q,))
        process.start()

    @property
    def sync(self):
        self._sync = True
        return self

    def load_scene(self, data_scene):
        objects, shaders, meshes = [], [], []
        base_scene = data_scene.scene

        for data_obj in data_scene.objects:
            obj = data_obj.obj
            serialized_obj = (obj.name, (), {"uniforms": obj.uniforms.as_dict() })
            objects.append(serialized_obj)

        for data_shader in data_scene.shaders:
            shader = data_shader.shader
            serialized_shader = (shader.name, (), {"uniforms": shader.uniforms.as_dict() })
            shaders.append(serialized_shader)

        for data_mesh in data_scene.meshes:
            mesh = data_mesh.mesh
            serialized_mesh = (mesh.name, (), {})
            meshes.append(serialized_mesh)

        serialized_scene = (("Objects", objects), ("Shaders", shaders), ("Meshes", meshes))
        self.sync_scene(serialized_scene)

    @lru_cache(maxsize=None)
    def __getattr__(self, name):
        if name in dir(DebugUIProcess):

            def send(*args, **kwargs):
                if not self.process.is_alive():
                    print("ERROR: remote process was closed")
                    return

                self.queue.put((name, args, kwargs))
                if self._sync: 
                    self.queue.join()
                self._sync = False

            return send
        else:
            raise AttributeError(f"No function named {name} in remote process")


class DebugUIProcess(object):

    def __init__(self, queue):
        self.queue = queue
        self.app = app = QApplication([])
        self.scene_data = None

        self.scene_tree = self.objects_form = self.shaders_form = self.meshes_form = None
        self.current_object = self.current_shader = self.current_mesh = None
        self.object_uniform_inspector = self.shader_uniform_inspector = None
        self.object_uniform_editor = self.shader_uniform_editor = None
        self.tabs = None

        self.window = QWidget()
        self.window.closeEvent = lambda evt: evt.ignore()
        self._init_window()

        self.timer = t = QTimer()
        t.setInterval(200)
        t.timeout.connect(lambda: self._read_queue() )
        t.start()

        app.exec_()

    def sync_scene(self, scene_data):
        tree, co, cs, cm = self.scene_tree, self.current_object, self.current_shader, self.current_mesh
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

        for obj_name, _, data in scene_data[0][1]:
            co.addItem(obj_name, data)

        for shader_name, _, data in scene_data[1][1]:
            cs.addItem(shader_name, data)

        for mesh_name, _, data in scene_data[2][1]:
            cm.addItem(mesh_name, data)

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
        else:
            print(f"Bad index {index}")
            return

        data = item_combo.currentData()

        if uniforms is not None:
            uniforms.load_uniforms(data["uniforms"])

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

        data = item_combo.currentData()
        uniform_name = inspector.item(row, 0).text()
        field_name = inspector.item(row, 1).text()
        value = data["uniforms"][uniform_name][field_name]
        uniforms.edit(f"{uniform_name}.{field_name}", value)

        uniforms.show()

    def close(self):
        del self.window.closeEvent
        self.window.close()

    def _read_queue(self):
        try:
            queue = self.queue
            name, argv, kwargs = queue.get_nowait()
            value = getattr(self, name)(*argv, **kwargs)
            queue.task_done()
        except Empty:
            pass

    def _init_window(self):
        w = self.window

        self.scene_tree = stree = QTreeWidget()
        stree.header().hide()

        self.current_object = cobj = QComboBox()
        self.object_uniform_inspector = uni1 = UniformInspector()
        self.object_uniform_editor = ed1 = UniformEditor()
        self.objects_form = of = QWidget()
        of_layout = QGridLayout()
        of_layout.addWidget(cobj, 0, 0)
        uni1.cellDoubleClicked.connect(self.edit_uniform)
        of_layout.addWidget(uni1, 1, 0)
        of_layout.addWidget(ed1, 2, 0)
        of.setLayout(of_layout)

        self.current_shader = cshader = QComboBox()
        self.shader_uniform_inspector = uni2 = UniformInspector()
        self.shader_uniform_editor = ed2 = UniformEditor()
        self.shaders_form = sf = QWidget()
        sf_layout = QGridLayout()
        sf_layout.addWidget(cshader, 0, 0)
        uni2.cellDoubleClicked.connect(self.edit_uniform)
        sf_layout.addWidget(uni2, 1, 0)
        sf_layout.addWidget(ed2, 2, 0)
        sf.setLayout(sf_layout)

        self.current_mesh = cmesh = QComboBox()
        self.meshes_form = mf = QWidget()
        mf_layout = QGridLayout()
        mf_layout.addWidget(cmesh, 0, 0)
        mf_layout.addWidget(QWidget(), 1, 0)
        mf.setLayout(mf_layout)

        self.tabs = tab = QTabWidget(w)
        tab.addTab(stree, "Scene")
        tab.addTab(of, "Objects")
        tab.addTab(sf, "Shaders")
        tab.addTab(mf, "Meshes")
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
                self.setItem(count, 2, QTableWidgetItem(repr(value)))
                count += 1

    def set_rows(self, uniforms):
        count = 0
        for name, fields in uniforms.items():
            count += 1
            count += len(fields)
        
        self.setRowCount(count-1)


class UniformEditor(QFrame):

    def __init__(self):
        super().__init__()
        
        l = QVBoxLayout()

        self.uniform_name = QLabel()

        l.addWidget(self.uniform_name)
        
        self.setFrameShape(QFrame.Box)
        self.setLayout(l)
        self.hide()

    def edit(self, name, value):
        self.uniform_name.setText(f"Uniform: {name}")
