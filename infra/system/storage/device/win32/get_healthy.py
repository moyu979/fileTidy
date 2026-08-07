# CHECK: AI生成 - win32 平台：获取设备健康状态
"""win32 —— 获取设备健康状态。"""

import subprocess

from domain.storage.device.enum import DeviceState


def get_healthy(path: str) -> DeviceState:
    """通过 PowerShell 获取磁盘健康状态。

    Args:
        path: 设备路径。

    Returns:
        DeviceState 枚举值。
    """
    ps = (
        'powershell -Command "'
        'Get-PhysicalDisk | '
        'Where-Object {$_.OperationalStatus -eq \'OK\'} | '
        'Select-Object -First 1 | '
        'Format-List OperationalStatus,HealthStatus"'
    )
    result = subprocess.run(ps, capture_output=True, text=True, shell=True)
    if "OK" in result.stdout or "Healthy" in result.stdout:
        return DeviceState.HEALTHY
    return DeviceState.UNKNOWN
