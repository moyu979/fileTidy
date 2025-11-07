"""
获取磁盘信息
"""

import os
import subprocess
import logging
from .isHdd import is_hdd
from .isSSD import is_ssd

logger = logging.getLogger(__name__)

# 注意：本方法未考虑移动硬盘（如 USB 设备），如有需要请自行扩展。
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


def get_size(dev_path):
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


def get_device_info(dev_path):
    """获取单个设备的完整信息"""
    serial = get_serial(dev_path)
    size = get_size(dev_path)
    device_name = os.path.basename(dev_path)
    
    return {
        "id": serial,
        "size": size,
        "path": dev_path
    }


def get_disk(path):
    """
    获取指定路径的磁盘信息。
    
    Args:
        path: 磁盘设备路径（如 /dev/sda 或 /dev/nvme0n1），必须提供。
    
    Returns:
        字典格式的磁盘信息，如果路径不存在或不是有效的磁盘设备则返回 None：
        {
            "id": "序列号值",
            "size": 容量字节数,
            "path": "/dev/设备名"
        }
    """
    if path is None:
        logger.error("路径参数不能为 None")
        return None
    
    path = str(path).strip()
    if not path:
        logger.error("路径参数不能为空")
        return None
    
    # 校验路径存在且为磁盘设备
    if not os.path.exists(path):
        logger.warning(f"设备路径不存在: {path}")
        return None
    
    # 使用 is_hdd 和 is_ssd 判断是否为有效的磁盘设备
    if not (is_hdd(path) or is_ssd(path)):
        logger.warning(f"不是有效的磁盘设备路径（非HDD或SSD）: {path}")
        return None
    
    return get_device_info(path)

def main():
    """测试磁盘信息获取功能"""
    print("=== 磁盘信息获取测试 ===\n")
    
    # 测试获取特定磁盘信息
    test_paths = ["/dev/sda", "/dev/nvme0n1", "/dev/sdb"]
    
    for test_path in test_paths:
        print(f"测试路径: {test_path}")
        try:
            disk = get_disk(test_path)
            if disk:
                print(f"  序列号: {disk['id'] or '未知'}")
                print(f"  容量: {disk['size'] or '未知'} 字节")
                if disk['size']:
                    size_gb = disk['size'] / (1024**3)
                    print(f"         ({size_gb:.2f} GB)")
                print(f"  路径: {disk['path']}")
            else:
                print(f"  无法获取设备信息或设备不存在")
            print()
        except Exception as e:
            print(f"  获取设备信息时出错: {e}")
            print()
    
    print("=== 测试完成 ===")
    

if __name__ == "__main__":
    main()
