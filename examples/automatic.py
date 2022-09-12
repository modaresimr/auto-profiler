import time

from ..

def f1():
    time.sleep(1)


def f2():
    time.sleep(1.5)


def show(p):
    print(Tree(p.root, span_unit='ms'))



@Profiler(timer_class=Timer, on_disable=show)
def hello():
    f1()
    f2()
    return "Hello World!"
