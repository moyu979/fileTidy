def get_capacity(dev_path):
    """获取设备容量（字节）"""
    try:
        # 使用 lsblk 获取设备大小
        result = subprocess.run([
            'lsblk', '-b', '-n', '-o', 'SIZE', dev_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.warning(f"lsblk命令执行失败，设备: {dev_path}, 错误: {result.stderr}")
            return None
        size_str = result.stdout.strip()
        if size_str:
            # 取第一行（通常是磁盘总容量）
            first_line = size_str.split('\n')[0]
            if first_line.isdigit():
                return int(first_line)
    except Exception as e:
        logger.warning(f"lsblk命令执行异常，设备: {dev_path}, 错误: {str(e)}")
        return None
    return None