# CHECK: AI生成 - device 平台无关工具：path|serial 归一化
"""device —— 平台无关工具：path|serial 归一化。"""

from infra.system.path_manager.is_path import is_path
from infra.system.runtime import current_platform


def as_device_path(value: str) -> str:
    """将「路径或序列号」归一化为设备路径。

    若 value 本身是路径则直接返回；否则视为序列号，
    通过当前平台的 get_path 解析为设备路径。

    Args:
        value: 设备路径或序列号。

    Returns:
        设备路径。

    Raises:
        ValueError: 无法将 value 解析为设备路径时抛出。
    """
    if is_path(value):
        return value
    path = current_platform().get_path(value)
    if path is None:
        raise ValueError(f"无法将 {value!r} 解析为设备路径（作为 serial 查询失败）")
    return path
