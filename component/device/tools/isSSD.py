import logging
from utils.confs import get_conf_manager

logger = logging.getLogger(__name__)


def is_ssd(device):
    """判断设备是否为SSD"""
    if get_conf_manager().get("system") == "windows":
        from .windows.isSSD import is_ssd as impl
    elif get_conf_manager().get("system") == "linux":
        from .linux.isSSD import is_ssd as impl
    elif get_conf_manager().get("system") == "macos":
        from .macos.isSSD import is_ssd as impl
    else:
        raise ValueError("不支持的系统")

    if impl is None:
        raise ValueError("获取平台对应的模块失败")

    return impl(device)

