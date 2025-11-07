import logging
from utils.confs import get_conf_manager

logger = logging.getLogger(__name__)


def is_tape(device):
    """判断设备是否为磁带"""
    if get_conf_manager().get("system") == "windows":
        from .windows.isTape import is_tape as impl
    elif get_conf_manager().get("system") == "linux":
        from .linux.isTape import is_tape as impl
    elif get_conf_manager().get("system") == "macos":
        from .macos.isTape import is_tape as impl
    else:
        raise ValueError("不支持的系统")

    if impl is None:
        raise ValueError("获取平台对应的模块失败")

    return impl(device)

