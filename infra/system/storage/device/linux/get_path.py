# CHECK: AI生成 - linux 平台：根据序列号获取设备路径
"""linux —— 根据序列号查找设备路径。"""

import json
import subprocess


def get_path(serial: str) -> str | None:
    """根据设备序列号查找设备路径。

    Args:
        serial: 设备序列号。

    Returns:
        设备挂载点路径，未找到时返回 None。
    """
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
