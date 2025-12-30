# 通过了初步校验

from utils.runCommand import run_command

def is_hdd(device: str) -> bool:
    """判断设备是否为HDD"""
    if not device:
        return False
    
    # 提取设备号
    device_num = None
    if device.isdigit():
        device_num = device
    elif device.startswith('PhysicalDrive'):
        device_num = device.replace('PhysicalDrive', '')
    elif device.startswith(r'\\.\PhysicalDrive'):
        device_num = device.replace(r'\\.\PhysicalDrive', '')
    else:
        return False
    
    # 使用 PowerShell 查询 MediaType
    ps_cmd = [
        'powershell', '-Command',
        f'$disk = Get-PhysicalDisk -DeviceNumber {device_num} -ErrorAction SilentlyContinue; '
        f'if ($disk) {{ Write-Output $disk.MediaType }}'
    ]
    code, out, err = run_command(ps_cmd)
    if code != 0 or not out.strip():
        return False
    
    return out.strip() == "HDD"

