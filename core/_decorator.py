from _Log import *

def init_decorator(func):
    def wrapper(clazz,args):
        print(f"init {clazz.__class__.__name__} start")
        func(clazz,args)
        print(f"init {clazz.__class__.__name__} finished")
    return wrapper

def call_decorator(func):
    def wrapper(clazz):
        print(f"run {clazz.__class__.__name__} start")
        func(clazz)
        print(f"run {clazz.__class__.__name__} finished")
    return wrapper