# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: AI生成 - linux 平台共享工具：lsblk 调用与容量解析
"""linux 平台共享工具 —— lsblk 调用与容量解析。"""

import json
import subprocess


def _lsblk(path: str) -> dict | None:
    """调用 lsblk --json 返回设备信息字典。

    Args:
        path: 设备路径或挂载点。

    Returns:
        匹配的设备信息字典，未找到时返回 None。

    Raises:
        RuntimeError: lsblk 命令执行失败时抛出。
    """
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
    """获取磁盘的详细信息字典。

    Args:
        path: 设备路径或挂载点。

    Returns:
        设备信息字典。

    Raises:
        RuntimeError: 无法通过 lsblk 找到设备时抛出。
    """
    dev = _lsblk(path)
    if dev is None:
        raise RuntimeError(f"无法通过 lsblk 找到设备: {path}")
    return dev


def _parse_size(s: str) -> int:
    """将 lsblk 的容量字符串转为字节数。

    Args:
        s: 容量字符串，如 "238.5G", "1T"。

    Returns:
        转换后的字节整数值。
    """
    s = s.upper().strip()
    multipliers = {"K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}
    for suffix, mul in multipliers.items():
        if s.endswith(suffix):
            return int(float(s[:-1]) * mul)
    return int(float(s))
