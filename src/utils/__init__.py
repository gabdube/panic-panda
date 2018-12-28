from .mat4 import Mat4
from .mat3 import Mat3
from .quat import Quat
from .vec3 import Vec3

import time


class TimeIt(object):

    def __enter__(self):
        self.time_enter = time.perf_counter()
    
    def __exit__(self, *args):
        time_diff = time.perf_counter() - self.time_enter
        print(f"{time_diff} elasped")
