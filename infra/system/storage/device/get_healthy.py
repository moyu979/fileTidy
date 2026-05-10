from infra.persistence.models import DeviceState


def get_healthy(path: str) -> DeviceState:
    """
    获取指定路径对应设备的健康状态（占位实现：由用户手动输入整数）。
    整数与 DeviceState 在 models.py 中的定义顺序一致：
      0 — HEALTHY（正常使用）
      1 — DANGER（有隐患但暂可用）
      2 — FAULT（故障不可用）
      3 — REMOVED（已移除/软删除）
    """
    states = list(DeviceState)
    lines = "\n".join(
        f"  {i} — {s.name}（{s.value}）"
        for i, s in enumerate(states)
    )
    raw = input(
        f"""
获取设备健康状态的功能尚未实现，请根据路径手动填入状态编码。
device_path: {path}
可选状态（整数须与下表一致）：
{lines}
请输入表示健康状态的整数 (0–{len(states) - 1})：
"""
    )
    idx = int(raw.strip())
    if idx < 0 or idx >= len(states):
        raise ValueError(
            f"健康状态编码须在 0–{len(states) - 1} 之间，与 DeviceState 定义顺序对应，收到: {idx}"
        )
    return states[idx]
