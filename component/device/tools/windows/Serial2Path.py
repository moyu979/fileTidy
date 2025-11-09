"""
根据给出的硬盘序列号，返回对应的设备路径，如果没有挂载这个序列号，返回None
"""

from utils.runCommand import run_command


def serial_to_path(serial):
    """
    根据序列号查找对应的设备路径
    
    Args:
        serial: 硬盘序列号
    
    Returns:
        str: 设备路径（如 \\.\PhysicalDrive0），如果未找到则返回 None
    """
    if not serial:
        return None
    
    # 使用 PowerShell 获取所有物理磁盘并查找匹配的序列号
    ps_cmd = [
        'powershell', '-Command',
        '$disks = Get-PhysicalDisk; '
        'foreach ($disk in $disks) { '
        '  if ($disk.SerialNumber -eq "' + serial + '") { '
        '    Write-Output $disk.DeviceNumber; '
        '    break '
        '  } '
        '}'
    ]
    
    code, out, err = run_command(ps_cmd)
    if code != 0 or not out.strip():
        return None
    
    device_num = out.strip()
    if device_num.isdigit():
        return rf'\\.\PhysicalDrive{device_num}'
    
    return None

