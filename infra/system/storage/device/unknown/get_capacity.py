# CHECK: AI生成 - unknown 平台：获取设备容量（占位）
"""unknown —— 获取设备容量（占位：手动输入）。"""

from infra.system.runtime import current_os


def get_capacity(path: str) -> int:
    """获取设备容量（占位实现：由用户手动输入字节数）。

    Args:
        path: 设备路径。

    Returns:
        设备容量（字节）。
    """
    capacity = input(
        f"获取设备容量的功能还没实现（{current_os()} 系统下），请手动填入\n"
        f"device_path is {path}\n"
        f"please input the capacity (in bytes, e.g., 1000000000): "
    )
    return int(capacity)
