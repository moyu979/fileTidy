import logging

# 确保在独立运行时也能导入 core 包
import os
import sys

from core.conf import conf

logger = logging.getLogger(__name__)

def _get_platform_impl():
    """根据配置加载平台实现模块，返回实现模块对象或 None。"""
    system = conf.get("system")
    if not system:
        logger.error("配置中未设置system，无法确定系统类型")
        return None

    system = system.lower()

    try:
        if system == "linux":
            from core.storage.tools.linux import detect_device_type as impl
            return impl
        else:
            logger.error(f"当前系统({system})不支持，仅支持linux")
            return None
    except Exception as exc:
        logger.error(f"加载平台实现失败: {exc}")
        return None


def is_disk_path(path):
    """判断是否磁盘路径。"""
    impl = _get_platform_impl()
    if impl is None:
        logger.error("获取平台对应的模块失败")
        return False
    return impl.is_disk_path(path)


def is_tape_path(path):
    """判断是否磁带路径。"""
    impl = _get_platform_impl()
    if impl is None:
        logger.error("获取平台对应的模块失败")
        return False
    return impl.is_tape_path(path)


def get_device_type(path):
    """返回设备类型："disk" | "tape"，无法识别返回 None。"""
    impl = _get_platform_impl()
    if impl is None:
        return None
    return impl.get_device_type(path)


__all__ = [
    "is_disk_path",
    "is_tape_path",
    "get_device_type",
]


