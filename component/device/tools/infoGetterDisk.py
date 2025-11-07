import logging
from utils.confs import get_conf_manager

logger = logging.getLogger(__name__)


def getDisk(path):
    """
    获取指定路径的磁盘信息。
    
    Args:
        path: 磁盘设备路径，格式取决于操作系统：
            - Linux: /dev/sda, /dev/nvme0n1 等
            - Windows: \\.\PhysicalDrive0, PhysicalDrive0, 0 等
            - macOS: /dev/disk0, disk0 等
    
    Returns:
        字典格式的磁盘信息，如果路径不存在或不是有效的磁盘设备则返回 None：
        {
            "id": "序列号值",
            "size": 容量字节数,
            "path": "设备路径"
        }
    """
    system = get_conf_manager().get("system")
    
    if system == "windows":
        from .windows.infoGetterDisk import get_disk as impl
    elif system == "linux":
        from .linux.infoGetterDisk import get_disk as impl
    elif system == "macos":
        from .macos.infoGetterDisk import get_disk as impl
    else:
        raise ValueError(f"不支持的系统: {system}")
    
    if impl is None:
        raise ValueError("获取平台对应的模块失败")
    
    return impl(path)


__all__ = [
    "getDisk",
]

