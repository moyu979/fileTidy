"""
获取挂载点的文件系统类型
"""

import os
import re
import subprocess
from .isMountPoint import is_mount_point

# 磁带设备模式：/dev/st0, st0 等
_TAPE_PATTERN = re.compile(r'^(/dev/)?st\d+$')


def get_filesystem(mount_point):
    """
    获取挂载点的文件系统类型
    
    Args:
        mount_point: 挂载点路径
    
    Returns:
        str: 文件系统类型（如 'ext4', 'xfs', 'ntfs', 'vfat', 'ltfs' 等），
             如果是磁带设备（如 /dev/st0）且不是挂载点，返回 'taptar'
             如果获取失败或不是挂载点则返回 None
    """
    try:
        # 先检查原始路径是否是磁带设备（避免路径规范化影响设备路径格式）
        # 即使 mount_point 可能为空，也要先 strip() 再检查
        original_path = mount_point.strip() if mount_point else ""
        is_tape_device = _TAPE_PATTERN.match(original_path) is not None
        
        # 如果不是磁带设备，检查是否为空
        if not is_tape_device and not original_path:
            return None
        
        # 规范化路径（用于挂载点检查）
        normalized_path = os.path.abspath(os.path.expanduser(mount_point))
        
        # 检查是否为挂载点
        is_mount = is_mount_point(normalized_path)
        
        # 如果是磁带设备但不是挂载点，返回 'taptar'
        if is_tape_device and not is_mount:
            return 'taptar'
        
        # 如果不是挂载点，返回 None
        if not is_mount:
            return None
        
        # 检查路径是否存在
        if not os.path.exists(normalized_path):
            return None
        
        # 方法1: 使用 df -T 命令获取文件系统类型
        try:
            result = subprocess.run(
                ['df', '-T', normalized_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    # 第一行是标题，第二行是数据
                    parts = lines[1].split()
                    if len(parts) >= 2:
                        filesystem_type = parts[1]
                        # 过滤掉特殊文件系统（如 tmpfs, devtmpfs 等，但保留它们）
                        return filesystem_type
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # 方法2: 读取 /proc/mounts 文件
        try:
            with open('/proc/mounts', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 3:
                        mount_path = parts[1]
                        filesystem_type = parts[2]
                        # 精确匹配或路径是挂载点的子路径
                        if mount_path == normalized_path or normalized_path.startswith(mount_path + '/'):
                            return filesystem_type
        except (IOError, OSError):
            pass
        
        # 方法3: 读取 /proc/self/mountinfo 文件（更详细的信息）
        try:
            with open('/proc/self/mountinfo', 'r') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 5:
                        mount_path = parts[4]
                        if mount_path == normalized_path or normalized_path.startswith(mount_path + '/'):
                            # 文件系统类型在后面的字段中，格式为 "type fstype"
                            for i, part in enumerate(parts):
                                if part == '-':
                                    # 在 '-' 之后是文件系统类型
                                    if i + 1 < len(parts):
                                        return parts[i + 1]
        except (IOError, OSError):
            pass
        
        return None
    except (OSError, IOError, AttributeError) as e:
        return None

