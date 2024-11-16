def say_begin_and_end(fun):
    def wrapper(*args, **kwargs):
        print(f"{fun.__name__} start")
        result=fun(*args, **kwargs)
        print(f"{fun.__name__} end")
        return result
    return wrapper


