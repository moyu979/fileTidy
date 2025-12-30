"""
获取挂载点的文件系统类型
"""

import os
import re
from .isMountPoint import is_mount_point

# 磁带设备模式：/dev/tape0, tape0 等
_TAPE_PATTERN = re.compile(r'^(/dev/)?tape\d+$', re.IGNORECASE)


def get_filesystem(mount_point):
    """
    获取挂载点的文件系统类型
    
    Args:
        mount_point: 挂载点路径
    
    Returns:
        str: 文件系统类型（如 'hfs', 'apfs', 'exfat', 'ntfs', 'ltfs' 等），
             如果是磁带设备（如 /dev/tape0）且不是挂载点，返回 'taptar'
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
        
        # 方法1: 使用 statfs 获取文件系统类型（macOS 特有）
        try:
            stat = os.statvfs(normalized_path)
            # macOS 的 statvfs 有 f_fstypename 属性
            if hasattr(stat, 'f_fstypename'):
                filesystem_type = stat.f_fstypename
                if filesystem_type:
                    # 转换为字符串并去除空字符
                    if isinstance(filesystem_type, bytes):
                        filesystem_type = filesystem_type.decode('utf-8', errors='ignore')
                    return filesystem_type.strip('\x00')
        except (OSError, IOError, AttributeError):
            pass
        
        # 方法2: 使用 diskutil info 命令（备选方案）
        try:
            import subprocess
            result = subprocess.run(
                ['diskutil', 'info', normalized_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if 'File System Personality:' in line or 'Type (Bundle):' in line:
                        # 提取文件系统类型
                        parts = line.split(':')
                        if len(parts) >= 2:
                            filesystem_type = parts[1].strip()
                            if filesystem_type:
                                return filesystem_type.lower()
        except (subprocess.TimeoutExpired, FileNotFoundError, ImportError):
            pass
        
        # 方法3: 读取 /etc/mtab 或使用 mount 命令
        try:
            import subprocess
            result = subprocess.run(
                ['mount'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    # mount 输出格式: device on mount_point (filesystem_type, options)
                    if normalized_path in line:
                        # 查找括号中的文件系统类型
                        if '(' in line and ')' in line:
                            bracket_content = line[line.find('(') + 1:line.find(')')]
                            parts = bracket_content.split(',')
                            if parts:
                                filesystem_type = parts[0].strip()
                                if filesystem_type:
                                    return filesystem_type.lower()
        except (subprocess.TimeoutExpired, FileNotFoundError, ImportError):
            pass
        
        return None
    except (OSError, IOError, AttributeError) as e:
        return None

