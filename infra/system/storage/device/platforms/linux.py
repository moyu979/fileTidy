"""
Linux 平台 —— 使用 lsblk + smartctl 获取设备信息。
"""

import json
import re
import subprocess

from domain.storage.device.enum import DeviceState


def _lsblk(path: str) -> dict | None:
    """调用 lsblk --json 返回设备信息字典。"""
    # 将挂载点转成对应的块设备
    result = subprocess.run(
        ["lsblk", "-J", "-o", "NAME,SERIAL,SIZE,ROTA,MOUNTPOINT,MODEL"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"lsblk 失败: {result.stderr.strip()}")

    data = json.loads(result.stdout)
    devices = data.get("blockdevices", [])

    # 展平嵌套结构（lsblk 输出是树形的）
    def flatten(devs):
        for d in devs:
            yield d
            yield from flatten(d.get("children", []))

    for dev in flatten(devices):
        mp = dev.get("mountpoint")
        name = dev.get("name", "")
        dev_path = f"/dev/{name}"
        if mp == path or dev_path == path:
            return dev
    return None


def _disk_info(path: str) -> dict:
    dev = _lsblk(path)
    if dev is None:
        raise RuntimeError(f"无法通过 lsblk 找到设备: {path}")
    return dev


def get_serial(path: str) -> str | None:
    info = _disk_info(path)
    return info.get("serial") or None


def get_capacity(path: str) -> int:
    """解析 SIZE 字段，如 \"238.5G\" → 字节数。"""
    info = _disk_info(path)
    raw = info.get("size", "0")
    return _parse_size(raw)


def _parse_size(s: str) -> int:
    """将 lsblk 的容量字符串转为字节数。"""
    s = s.upper().strip()
    multipliers = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
    for suffix, mul in multipliers.items():
        if s.endswith(suffix):
            return int(float(s[:-1]) * mul)
    return int(float(s))


def get_type(path: str) -> str:
    info = _disk_info(path)
    rota = info.get("rota")
    model = (info.get("model") or "").lower()
    if "sd" in model or "flash" in model:
        return "tf_sd_card"
    if rota == 0:   # 非旋转 → SSD
        return "ssd"
    return "hdd"


def get_healthy(path: str) -> DeviceState:
    """通过 smartctl 获取健康状态（需安装 smartmontools）。"""
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


def get_path(serial: str) -> str | None:
    result = subprocess.run(
        ["lsblk", "-J", "-o", "NAME,SERIAL,MOUNTPOINT"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    data = json.loads(result.stdout)

    def flatten(devs):
        for d in devs:
            yield d
            yield from flatten(d.get("children", []))

    for dev in flatten(data.get("blockdevices", [])):
        if dev.get("serial") == serial:
            return dev.get("mountpoint") or None
    return None


def is_disk(path: str) -> bool:
    try:
        _disk_info(path)
        return True
    except RuntimeError:
        return False
