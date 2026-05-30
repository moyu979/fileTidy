"""
Windows 平台 —— 使用 wmic / PowerShell 获取设备信息。
"""

import re
import subprocess

from domain.storage.device.enum import DeviceState


def _wmic(cmd: str) -> list[dict[str, str]]:
    """执行 wmic 命令并返回结构化结果。"""
    full_cmd = f"wmic {cmd} /FORMAT:CSV"
    result = subprocess.run(full_cmd, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        raise RuntimeError(f"wmic 失败: {result.stderr.strip()}")

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        return []

    headers = [h.strip() for h in lines[0].split(",")][1:]  # 去掉 Node
    rows = []
    for line in lines[1:]:
        values = [v.strip() for v in line.split(",")][1:]
        rows.append(dict(zip(headers, values)))
    return rows


def _get_drive_by_path(path: str) -> dict | None:
    """根据路径找到对应的物理磁盘。"""
    # 通过 mountvol 或 PowerShell 获取卷→盘符映射
    ps = (
        f'powershell -Command "'
        f'Get-Volume -FilePath \'{path}\' | '
        f'Select-Object -ExpandProperty DriveLetter"'
    )
    result = subprocess.run(ps, capture_output=True, text=True, shell=True)
    drive_letter = result.stdout.strip()
    if not drive_letter:
        raise RuntimeError(f"无法找到路径对应的卷: {path}")

    drives = _wmic("diskdrive get SerialNumber,Size,MediaType,Index")
    for d in drives:
        # 通过盘符找对应物理磁盘
        parts = _wmic(f"partition where DiskIndex={d['Index']} get DeviceID")
        for p in parts:
            logical = _wmic(
                f"logicaldisk where DeviceID=\"{drive_letter}:\" "
                f"assoc /assocclass:Win32_LogicalDiskToPartition"
            )
            if logical:
                return d
    return None


def get_serial(path: str) -> str | None:
    drive = _get_drive_by_path(path)
    if drive:
        return drive.get("SerialNumber", "").strip() or None
    return None


def get_capacity(path: str) -> int:
    drive = _get_drive_by_path(path)
    if drive and "Size" in drive:
        return int(drive["Size"])
    raise ValueError(f"无法获取容量: {path}")


def get_type(path: str) -> str:
    drive = _get_drive_by_path(path)
    if drive:
        media = (drive.get("MediaType") or "").lower()
        if "ssd" in media or "solid" in media:
            return "ssd"
        if "external" in media or "removable" in media:
            if drive.get("Size", "0") < 256 * 1024**3:  # < 256GB 可能 TF
                return "tf_sd_card"
        return "hdd"
    raise ValueError(f"无法获取类型: {path}")


def get_healthy(path: str) -> DeviceState:
    """通过 PowerShell 获取磁盘健康状态。"""
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


def get_path(serial: str) -> str | None:
    drives = _wmic("diskdrive where SerialNumber=\"" + serial + "\" get Index")
    if not drives:
        return None
    idx = drives[0].get("Index", "")
    parts = _wmic(f"partition where DiskIndex={idx} get DeviceID")
    if not parts:
        return None
    logical = _wmic(
        f"logicaldisk where "
        f"assoc /assocclass:Win32_LogicalDiskToPartition"
    )
    # 解析关联结果找到盘符
    for l in logical:
        for k, v in l.items():
            if ":" in v and len(v.strip()) == 2:  # C:, D: ...
                return v.strip()
    return None


def is_disk(path: str) -> bool:
    try:
        _get_drive_by_path(path)
        return True
    except (RuntimeError, subprocess.TimeoutExpired):
        return False
