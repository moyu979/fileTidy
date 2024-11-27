import logging

def say_begin_and_end(fun):
    def wrapper(*args, **kwargs):
        logging.debug(f"{fun.__name__} start")
        result=fun(*args, **kwargs)
        logging.debug(f"{fun.__name__} end")
        return result
    return wrapper


def decorate_class_methods(cls):
    for attr_name, attr_value in cls.__dict__.items():
        if callable(attr_value):  # 如果属性是一个方法
            decorated_method = say_begin_and_end(attr_value)  # 给方法添加修饰器
            setattr(cls, attr_name, decorated_method)  # 替换原有方法
    return cls