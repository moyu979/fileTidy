# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: AI生成 - linux 平台：获取设备健康状态
"""linux —— 获取设备健康状态。"""

import subprocess

from domain.storage.device.enum import DeviceState

from ._common import _disk_info


def get_healthy(path: str) -> DeviceState:
    """通过 smartctl 获取设备健康状态（需安装 smartmontools）。

    Args:
        path: 设备路径。

    Returns:
        DeviceState 枚举值：HEALTHY、FAULT 或 UNKNOWN。
    """
    # 先找原始设备名
    info = _disk_info(path)
    dev_path = f"/dev/{info['name']}"
    result = subprocess.run(
        ["smartctl", "-H", dev_path],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return DeviceState.UNKNOWN
    if "PASSED" in result.stdout:
        return DeviceState.HEALTHY
    if "FAILED" in result.stdout:
        return DeviceState.FAULT
    return DeviceState.UNKNOWN
