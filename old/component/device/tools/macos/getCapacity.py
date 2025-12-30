from component.device.tools.macos.getPath import get_device_path


def get_capacity(dev_path):
    """获取设备容量（字节）"""
    try:
        # 规范化设备路径为 /dev/diskN 格式
        
        device_path = get_device_path(dev_path)
        # 使用 diskutil info 获取容量
        cmd = ["diskutil", "info", device_path]
        code, out, err = run_command(cmd)
        if code != 0:
            logger.warning(f"获取容量失败，设备: {device_path}, 错误: {err}")
            return None
        
        # 从 diskutil 输出中提取容量
        for line in out.splitlines():
            if "Disk Size:" in line or "Total Size:" in line:
                # 格式通常是 "Disk Size: 500.1 GB (500107862016 Bytes)"
                # 提取括号中的字节数
                if "(" in line and "Bytes" in line:
                    parts = line.split("(")
                    if len(parts) > 1:
                        size_part = parts[1].split("Bytes")[0].strip()
                        # 移除逗号并转换为整数
                        size_str = size_part.replace(",", "").strip()
                        if size_str.isdigit():
                            return int(size_str)
    except Exception as e:
        logger.warning(f"获取容量异常，设备: {dev_path}, 错误: {str(e)}")
        return None
    return None