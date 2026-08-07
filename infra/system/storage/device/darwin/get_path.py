# CHECK: AI生成 - darwin 平台：根据序列号获取设备路径
"""darwin —— 根据序列号查找设备路径。"""

import re
import subprocess

from ._common import _disk_info


def get_path(serial: str) -> str | None:
    """根据设备序列号查找设备路径。

    遍历所有磁盘，匹配序列号后返回挂载点。

    Args:
        serial: 设备序列号。

    Returns:
        设备挂载点路径，未找到时返回 None。
    """
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
