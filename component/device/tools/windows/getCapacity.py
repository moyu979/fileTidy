def get_capacity(dev_path):
    """获取设备容量（字节）"""
    try:
        # 规范化设备路径，提取设备号
        device_num = None
        if dev_path.isdigit():
            device_num = dev_path
        elif dev_path.startswith('PhysicalDrive'):
            device_num = dev_path.replace('PhysicalDrive', '')
        elif dev_path.startswith(r'\\.\PhysicalDrive'):
            device_num = dev_path.replace(r'\\.\PhysicalDrive', '')
        else:
            return None
        
        # 使用 PowerShell 获取容量（字节）
        ps_cmd = [
            'powershell', '-Command',
            f'$disk = Get-PhysicalDisk -DeviceNumber {device_num} -ErrorAction SilentlyContinue; '
            f'if ($disk) {{ Write-Output $disk.Size }}'
        ]
        code, out, err = run_command(ps_cmd)
        if code != 0 or not out.strip():
            logger.warning(f"获取容量失败，设备: {dev_path}, 错误: {err}")
            return None
        size_str = out.strip()
        if size_str.isdigit():
            return int(size_str)
    except Exception as e:
        logger.warning(f"获取容量异常，设备: {dev_path}, 错误: {str(e)}")
        return None
    return None