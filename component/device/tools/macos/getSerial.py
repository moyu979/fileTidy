def get_serial(dev_path):
    """获取设备序列号"""
    try:
        # 规范化设备路径为 /dev/diskN 格式
        if dev_path.startswith('/dev/disk'):
            device_path = dev_path
        elif dev_path.startswith('disk'):
            device_path = f'/dev/{dev_path}'
        else:
            return None
        
        # 优先使用 smartctl 获取序列号
        cmd = ["sudo", "smartctl", "-i", device_path]
        code, out, err = run_command(cmd)
        if code == 0:
            # 从 smartctl 输出中提取序列号
            for line in out.splitlines():
                if "Serial Number:" in line or "Serial number:" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        return parts[1].strip()
        
        # smartctl 不可用，使用 diskutil
        cmd = ["diskutil", "info", device_path]
        code, out, err = run_command(cmd)
        if code != 0:
            logger.warning(f"获取序列号失败，设备: {device_path}, 错误: {err}")
            return None
        
        # 从 diskutil 输出中提取序列号
        for line in out.splitlines():
            if "Volume UUID:" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    return parts[1].strip()
            elif "Disk / Partition UUID:" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    return parts[1].strip()
    except Exception as e:
        logger.warning(f"获取序列号异常，设备: {dev_path}, 错误: {str(e)}")
        return None
    return None