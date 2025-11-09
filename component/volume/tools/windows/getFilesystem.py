"""
获取挂载点的文件系统类型
"""

import os
import re
import ctypes
from ctypes import wintypes
from .isMountPoint import is_mount_point

# 磁带设备模式：\\.\Tape0, Tape0 等
_TAPE_PATTERN = re.compile(r'^(\\\\.\\)?Tape\d+$', re.IGNORECASE)


def get_filesystem(mount_point):
    """
    获取挂载点的文件系统类型
    
    Args:
        mount_point: 挂载点路径（如 C:\ 或挂载的目录）
    
    Returns:
        str: 文件系统类型（如 'NTFS', 'FAT32', 'exFAT', 'ReFS', 'ltfs' 等），
             如果是磁带设备（如 \\.\Tape0）且不是挂载点，返回 'taptar'
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
        
        # 使用 Windows API GetVolumeInformation 获取文件系统类型
        kernel32 = ctypes.windll.kernel32
        
        # 准备缓冲区
        volume_name_buffer = ctypes.create_unicode_buffer(wintypes.MAX_PATH + 1)
        filesystem_name_buffer = ctypes.create_unicode_buffer(wintypes.MAX_PATH + 1)
        volume_serial_number = wintypes.DWORD()
        max_component_length = wintypes.DWORD()
        filesystem_flags = wintypes.DWORD()
        
        # 规范化路径，确保以反斜杠结尾（Windows API 要求）
        root_path = os.path.normpath(normalized_path)
        if not root_path.endswith('\\'):
            root_path = root_path + '\\'
        
        # 调用 GetVolumeInformationW
        success = kernel32.GetVolumeInformationW(
            root_path,
            volume_name_buffer,
            wintypes.MAX_PATH + 1,
            ctypes.byref(volume_serial_number),
            ctypes.byref(max_component_length),
            ctypes.byref(filesystem_flags),
            filesystem_name_buffer,
            wintypes.MAX_PATH + 1
        )
        
        if success:
            filesystem_type = filesystem_name_buffer.value
            if filesystem_type:
                return filesystem_type
        
        return None
    except (OSError, IOError, AttributeError, ctypes.ArgumentError) as e:
        return None

