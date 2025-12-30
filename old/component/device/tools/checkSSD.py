import logging
from utils.confs import get_conf_manager

logger = logging.getLogger(__name__)


def ssd_check(device, scan_blocks=False):
    """
    检查SSD健康状态，返回 'health'（健康）、'danger'（警告）、None（检查失败）
    
    Args:
        device: SSD设备路径，格式取决于操作系统：
            - Linux: /dev/sda, /dev/nvme0n1 等
            - Windows: \\.\PhysicalDrive0, PhysicalDrive0, 0 等
            - macOS: /dev/disk0, disk0 等
        scan_blocks: 是否开启坏道扫描，默认为False（SSD无需坏道扫描）
    
    Returns:
        str: 'health' 表示健康，'danger' 表示有警告
        None: 检查失败或发生错误
    """
    system = get_conf_manager().get("system")
    
    if system == "windows":
        from .windows.checkSSD import ssd_check as impl
    elif system == "linux":
        from .linux.checkSSD import ssd_check as impl
    elif system == "macos":
        from .macos.checkSSD import ssd_check as impl
    else:
        raise ValueError(f"不支持的系统: {system}")
    
    if impl is None:
        raise ValueError("获取平台对应的模块失败")
    
    return impl(device, scan_blocks)


__all__ = [
    "checkSSD",
]

