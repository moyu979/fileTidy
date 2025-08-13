import os
import subprocess
import re
import logging

# 配置日志
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
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


def get_disk(path=None):
    """
    获取磁盘信息。
    - path: 指定磁盘路径（如 /dev/sda 或 /dev/nvme0n1），只返回该磁盘的信息。
    - path=None: 遍历所有磁盘（包括 /dev/sd* 和 /dev/nvme*），返回包含磁盘信息的字典列表。
    
    返回格式：
    [
        {
            "id": "序列号值",
            "size": 容量字节数,
            "path": "/dev/设备名"
        },
        ...
    ]
    """

    if path is not None and path.strip():
        # 如果指定了路径，只返回该设备的信息
        if os.path.exists(path):
            return [get_device_info(path)]
        else:
            return None
    else:
        # 遍历所有磁盘设备
        disk_list = []
        # 使用正则表达式匹配磁盘设备，排除分区
        # sd设备：sda, sdb, sdaa, sdab等（不包含数字）
        # nvme设备：nvme0n1, nvme1n1等
        disk_pattern = re.compile(r'^(sd[a-z]+|nvme\d+n\d+)$')
        
        for dev in os.listdir('/dev'):
            if disk_pattern.match(dev):
                dev_path = os.path.join('/dev', dev)
                if os.path.exists(dev_path):
                    device_info = get_device_info(dev_path)
                    disk_list.append(device_info)
        return disk_list

def main():
    """测试磁盘信息获取功能"""
    print("=== 磁盘信息获取测试 ===\n")
    
    # 测试1：获取所有磁盘信息
    print("1. 获取所有磁盘信息：")
    try:
        all_disks = get_disk()
        if all_disks:
            for i, disk in enumerate(all_disks, 1):
                print(f"   磁盘 {i}:")
                print(f"     序列号: {disk['id'] or '未知'}")
                print(f"     容量: {disk['size'] or '未知'} 字节")
                if disk['size']:
                    # 转换为更易读的格式
                    size_gb = disk['size'] / (1024**3)
                    size_mb = disk['size'] / (1024**2)
                    if size_gb >= 1:
                        print(f"           ({size_gb:.2f} GB)")
                    else:
                        print(f"           ({size_mb:.2f} MB)")
                print(f"     路径: {disk['path']}")
                print()
        else:
            print("   未找到任何磁盘设备")
    except Exception as e:
        print(f"   获取所有磁盘信息时出错: {e}")
    
    print("-" * 50)
    
    # 测试2：获取特定磁盘信息（如果存在）
    print("2. 测试获取特定磁盘信息：")
    test_paths = ["/dev/sda", "/dev/nvme0n1", "/dev/sdb"]
    
    for test_path in test_paths:
        print(f"   测试路径: {test_path}")
        try:
            if os.path.exists(test_path):
                specific_disk = get_disk(test_path)
                if specific_disk:
                    disk = specific_disk[0]
                    print(f"     序列号: {disk['id'] or '未知'}")
                    print(f"     容量: {disk['size'] or '未知'} 字节")
                    if disk['size']:
                        size_gb = disk['size'] / (1024**3)
                        print(f"           ({size_gb:.2f} GB)")
                    print(f"     路径: {disk['path']}")
                else:
                    print(f"     无法获取设备信息")
            else:
                print(f"     设备不存在")
            print()
        except Exception as e:
            print(f"     获取设备信息时出错: {e}")
    
    print("=== 测试完成 ===")
    

if __name__ == "__main__":
    main()
