# CHECK: AI生成 - device 转发：判断路径是否为磁盘
"""device —— 转发到当前平台：判断路径是否为磁盘。"""

from infra.system.runtime import current_platform

from ._util import as_device_path


def is_disk(path_or_serial: str) -> bool:
    """判断路径是否为磁盘（支持传路径或序列号）。

    Args:
        path_or_serial: 设备路径或序列号。

    Returns:
        是磁盘返回 True，否则返回 False。

    Raises:
        ValueError: 无法将入参解析为设备路径时抛出。
    """
    return current_platform().is_disk(as_device_path(path_or_serial))
