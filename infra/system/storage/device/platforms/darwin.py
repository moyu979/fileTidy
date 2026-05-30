"""
macOS 平台 —— 使用 diskutil info 获取设备信息。
"""

import re
import subprocess

from domain.storage.device.enum import DeviceState


def _disk_info(path: str) -> dict[str, str]:
    """调用 diskutil info 并返回 key:value 字典。"""
    result = subprocess.run(
        ["diskutil", "info", path],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"diskutil info 失败 ({path}): {result.stderr.strip()}")

    info: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            info[key.strip()] = value.strip()
    return info


def get_serial(path: str) -> str | None:
    """从 Disk / Partition UUID 行获取。如果是分区则返回 None。"""
    info = _disk_info(path)
    # 整盘才有 Serial Number，分区没有
    if "Serial Number" in info:
        return info["Serial Number"] or None
    return None


def get_capacity(path: str) -> int:
    """解析 Disk Size 行括号内的字节数。"""
    info = _disk_info(path)
    raw = info.get("Disk Size", "")
    match = re.search(r"\((\d+)\s+Bytes\)", raw)
    if match:
        return int(match.group(1))
    raise ValueError(f"无法解析容量: {path}")


def get_type(path: str) -> str:
    """根据 Solid State / Removable Media 判断类型。"""
    info = _disk_info(path)
    solid = info.get("Solid State", "").lower()
    removable = info.get("Removable Media", "").lower()

    if removable == "removable":
        return "tf_sd_card"
    if solid == "yes":
        return "ssd"
    return "hdd"  # 默认 HDD


def get_healthy(path: str) -> DeviceState:
    """解析 SMART Status。"""
    info = _disk_info(path)
    status = info.get("SMART Status", "").lower()
    if status == "verified":
        return DeviceState.HEALTHY
    if status == "failing":
        return DeviceState.FAULT
    if status in ("unsupported", "not supported"):
        return DeviceState.UNKNOWN
    return DeviceState.UNKNOWN


def get_path(serial: str) -> str | None:
    """遍历所有磁盘，匹配序列号后返回挂载点。"""
    result = subprocess.run(
        ["diskutil", "list"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None

    # 获取所有 disk identifier
    disks = re.findall(r"/dev/disk\d+", result.stdout)
    for disk in disks:
        try:
            info = _disk_info(disk)
            if info.get("Serial Number", "").strip() == serial:
                return info.get("Mount Point") or None
        except RuntimeError:
            continue
    return None


def is_disk(path: str) -> bool:
    """判断路径是否可被 diskutil 识别。"""
    try:
        _disk_info(path)
        return True
    except (RuntimeError, subprocess.TimeoutExpired):
        return False
