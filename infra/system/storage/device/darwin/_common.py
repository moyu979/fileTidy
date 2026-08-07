# CHECK: AI生成 - darwin 平台共享工具：diskutil 调用
"""darwin 平台共享工具 —— diskutil 调用。"""

import subprocess


def _disk_info(path: str) -> dict[str, str]:
    """调用 diskutil info 获取设备信息字典。

    Args:
        path: 设备路径。

    Returns:
        设备信息键值对字典。

    Raises:
        RuntimeError: diskutil 命令执行失败时抛出。
    """
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
