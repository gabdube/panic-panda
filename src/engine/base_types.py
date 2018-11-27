from collections import namedtuple

Queue = namedtuple("Queue", ("handle", "family"))
ImageAndView = namedtuple("ImageAndView", ("image", "view"))

def name_generator(base):
    i = 0
    while True:
        i += 1
        yield f"{base}_{i}"
