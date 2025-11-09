"""
输入磁盘路径，返回磁盘序列号
"""

import subprocess


def get_id(dev_path):
    """输入磁盘路径，返回磁盘序列号"""
    try:
        # 使用 udevadm 获取序列号
        result = subprocess.run([
            'udevadm', 'info', '--query=property', '--name', dev_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        
        if result.returncode != 0:
            return None
        
        for line in result.stdout.splitlines():
            if line.startswith('ID_SERIAL='):
                return line.split('=', 1)[1]
    except Exception:
        return None
    return None

