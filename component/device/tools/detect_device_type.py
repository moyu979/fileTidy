import os
import sys
import logging
from utils.confs import get_conf_manager
logger = logging.getLogger(__name__)

def is_disk_path(path):
    """判断是否磁盘路径。"""
    if get_conf_manager().get("system") == "windows":
        from .windows.detect_device_type import is_disk_path as impl
    elif get_conf_manager().get("system") == "linux":
        from .linux.detect_device_type import is_disk_path as impl
    elif get_conf_manager().get("system") == "macos":
        from .macos.detect_device_type import is_disk_path as impl
    else:
        raise ValueError("不支持的系统")

    if impl is None:
        raise ValueError("获取平台对应的模块失败")

    return impl(path)

def is_tape_path(path):
    """判断是否磁带路径。"""
    if get_conf_manager().get("system") == "windows":
        from .windows.detect_device_type import is_tape_path as impl
    elif get_conf_manager().get("system") == "linux":
        from .linux.detect_device_type import is_tape_path as impl
    elif get_conf_manager().get("system") == "macos":
        from .macos.detect_device_type import is_tape_path as impl
    else:
        raise ValueError("不支持的系统")

    if impl is None:
        raise ValueError("获取平台对应的模块失败")

    return impl(path)


def get_device_type(path):
    """返回设备类型："disk" | "tape"，无法识别返回 None。"""
    if get_conf_manager().get("system") == "windows":
        from .windows.detect_device_type import get_device_type as impl
    elif get_conf_manager().get("system") == "linux":
        from .linux.detect_device_type import get_device_type as impl
    elif get_conf_manager().get("system") == "macos":
        from .macos.detect_device_type import get_device_type as impl
    else:
        raise ValueError("不支持的系统")

    if impl is None:
        raise ValueError("获取平台对应的模块失败")

    return impl(path)