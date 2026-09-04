# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: AI生成 - win32 平台共享工具：wmic/PowerShell 调用
"""win32 平台共享工具 —— wmic / PowerShell 调用。"""

import subprocess


def _wmic(cmd: str) -> list[dict[str, str]]:
    """执行 wmic 命令并返回结构化结果。

    Args:
        cmd: wmic 命令参数字符串。

    Returns:
        键值对字典列表，每项对应一行结果。

    Raises:
        RuntimeError: wmic 命令执行失败时抛出。
    """
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
    """根据路径找到对应的物理磁盘。

    Args:
        path: 设备路径或挂载点。

    Returns:
        物理磁盘信息字典，未找到时返回 None。

    Raises:
        RuntimeError: 无法找到路径对应的卷时抛出。
    """
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
