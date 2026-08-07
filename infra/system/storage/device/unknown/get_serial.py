# CHECK: AI生成 - unknown 平台：获取设备序列号（占位）
"""unknown —— 获取设备序列号（占位：手动输入）。"""

from infra.system.runtime import current_os


def get_serial(path: str) -> str | None:
    """获取设备序列号（占位实现：由用户手动输入）。

    Args:
        path: 设备路径。

    Returns:
        设备序列号，输入空字符则返回 None。
    """
    serial = input(
        f"get serial for {path}（{current_os()} 系统下）的功能还没实现，"
        f"请手动填入，输入空字符以做 None: "
    )
    if serial == "":
        return None
    return serial
