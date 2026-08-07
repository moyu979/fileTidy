# CHECK: AI生成 - unknown 平台：获取设备健康状态（占位）
"""unknown —— 获取设备健康状态（占位：手动输入编码）。"""

from domain.storage.device.enum import DeviceState
from infra.system.runtime import current_os


def get_healthy(path: str) -> DeviceState:
    """获取设备健康状态（占位实现：由用户手动输入整数）。

    整数与 DeviceState 的定义顺序一致：
      0 — UNKNOWN（未知，默认）
      1 — HEALTHY（正常使用）
      2 — DANGER（有隐患但暂可用）
      3 — FAULT（故障不可用）
      4 — REMOVED（已移除/软删除）

    Args:
        path: 设备路径。

    Returns:
        DeviceState 枚举值。

    Raises:
        ValueError: 输入的状态编码越界时抛出。
    """
    states = list(DeviceState)
    lines = "\n".join(
        f"  {i} — {s.name}（{s.value}）"
        for i, s in enumerate(states)
    )
    raw = input(
        f"获取设备健康状态的功能尚未实现（{current_os()} 系统下），请手动填入状态编码。\n"
        f"device_path: {path}\n"
        f"可选状态（整数须与下表一致）：\n{lines}\n"
        f"请输入表示健康状态的整数 (0–{len(states) - 1})："
    )
    idx = int(raw.strip())
    if idx < 0 or idx >= len(states):
        raise ValueError(
            f"健康状态编码须在 0–{len(states) - 1} 之间，与 DeviceState 定义顺序对应，收到: {idx}"
        )
    return states[idx]
