"""
输入磁盘路径，返回磁盘序列号
"""

import subprocess


def get_serial(dev_path):
    """获取设备序列号"""
    try:
        # 使用 udevadm 获取序列号
        result = subprocess.run([
            'udevadm', 'info', '--query=property', '--name', dev_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.warning(f"udevadm命令执行失败，设备: {dev_path}, 错误: {result.stderr}")
            return None
        for line in result.stdout.splitlines():
            if line.startswith('ID_SERIAL='):
                return line.split('=', 1)[1]
    except Exception as e:
        logger.warning(f"udevadm命令执行异常，设备: {dev_path}, 错误: {str(e)}")
        return None
    return None

