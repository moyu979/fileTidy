# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: AI生成 - unknown 平台：获取设备路径（占位）
"""unknown —— 获取设备路径（占位：手动输入）。"""

from infra.system.runtime import current_os


def get_path(serial: str) -> str | None:
    """获取设备路径（占位实现：由用户手动输入）。

    Args:
        serial: 设备序列号。

    Returns:
        设备路径，输入空字符则返回 None。
    """
    path = input(
        f"get device path for {serial}（{current_os()} 系统下）的功能还没实现，"
        f"请手动填入，输入空字符以做 None: "
    )
    if path == "":
        return None
    return path
