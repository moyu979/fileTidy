# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: AI生成 - unknown 平台：判断路径是否为磁盘（占位）
"""unknown —— 判断路径是否为磁盘（占位：手动确认）。"""

from infra.system.runtime import current_os


def is_disk(path: str) -> bool:
    """判断路径是否为磁盘（占位实现：由用户手动确认）。

    Args:
        path: 待检查的路径。

    Returns:
        是磁盘挂载点返回 True，否则返回 False。
    """
    answer = input(
        f"检查路径是否是磁盘的挂载点（{current_os()} 系统下）的功能还没写好，请手动输入：\n"
        f"yes: 是\nno: 否\n"
    )
    return answer.strip().lower() in ("yes", "y")
