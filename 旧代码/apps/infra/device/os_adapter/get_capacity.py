from apps.common.config.config import config_manager

def get_capacity(device_path):
    """判断设备是否为HDD"""
    if config_manager.get("system") == "Windows":
        from .windows.get_capacity import get_capacity as impl
    elif config_manager.get("system") == "Linux":
        from .linux.get_capacity import get_capacity as impl
    elif config_manager.get("system") == "macos":
        from .macos.get_capacity import get_capacity as impl
    else:
        raise ValueError("不支持的系统")

    if impl is None:
        raise ValueError("获取平台对应的模块失败")

    return impl(device_path)

__all__ = [
    "get_type",
]