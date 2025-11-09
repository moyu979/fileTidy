"""
输入磁盘路径，返回磁盘序列号
"""

from utils.runCommand import run_command


def get_serial(dev_path):
    """输入磁盘路径，返回磁盘序列号"""

    if dev_path.isdigit():
        dev_path = rf'\\.\PhysicalDrive{dev_path}'
    elif dev_path.startswith('PhysicalDrive'):
        dev_path = rf'\\.\{dev_path}'
    elif dev_path.startswith(r'\\.\PhysicalDrive'):
        dev_path = dev_path
    else:
        dev_path = dev_path

    # 提取设备号
    if dev_path.isdigit():
        device_num = dev_path
    elif dev_path.startswith('PhysicalDrive'):
        device_num = dev_path.replace('PhysicalDrive', '')
    elif dev_path.startswith(r'\\.\PhysicalDrive'):
        device_num = dev_path.replace(r'\\.\PhysicalDrive', '')
    else:
        return None
    
    # 使用 PowerShell 获取序列号
    ps_cmd = [
        'powershell', '-Command',
        f'$disk = Get-PhysicalDisk -DeviceNumber {device_num} -ErrorAction SilentlyContinue; '
        f'if ($disk) {{ Write-Output $disk.SerialNumber }}'
    ]
    code, out, err = run_command(ps_cmd)
    if code != 0 or not out.strip():
        return None
    return out.strip()