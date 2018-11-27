from multiprocessing import Process, JoinableQueue
from queue import Empty
from PyQt5.QtWidgets import QApplication, QWidget, QTabWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import QTimer
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

        for data_shader in data_scene.shaders:
            shader = data_shader.shader
            serialized_shader = (shader.name, ())
            shaders.append(serialized_shader)

        for data_mesh in data_scene.meshes:
            mesh = data_mesh.mesh
            serialized_mesh = (mesh.name, ())
            meshes.append(serialized_mesh)

        for data_obj in data_scene.objects:
            obj = data_obj.obj
            serialized_obj = (obj.name, ())
            objects.append(serialized_obj)

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

        self.timer = t = QTimer()
        t.setInterval(200)
        t.timeout.connect(lambda: self._read_queue() )
        t.start()

        self.scene_tree = self.objects_form = self.shaders_form = self.meshes_form = None

        self.window = w = QWidget()
        self._init_window(w)

        app.exec_()

    def sync_scene(self, scene_data):
        tree = self.scene_tree
        tree.clear()

        parent = tree

        def iter_data(data):
            nonlocal parent

            for name, children in data:
                old_parent = parent
                parent = QTreeWidgetItem(parent, [name])
                iter_data(children)
                parent = old_parent

        iter_data(scene_data)

    def close(self):
        self.window.close()

    def _read_queue(self):
        try:
            queue = self.queue
            name, argv, kwargs = queue.get_nowait()
            value = getattr(self, name)(*argv, **kwargs)
            queue.task_done()
        except Empty:
            pass

    def _init_window(self, w):
        self.scene_tree = stree = QTreeWidget()
        stree.header().hide()

        self.objects_form = of = QWidget()
        self.shaders_form = sf = QWidget()
        self.meshes_form = mf = QWidget()

        tab = QTabWidget(w)
        tab.addTab(stree, "Scene")
        tab.addTab(of, "Objects")
        tab.addTab(sf, "Shaders")
        tab.addTab(mf, "Meshes")

        l = QVBoxLayout()
        l.addWidget(tab)

        w.setLayout(l)
        w.resize(450, 400)
        w.move(100, 300)
        w.setWindowTitle('Debug')
        w.show()
