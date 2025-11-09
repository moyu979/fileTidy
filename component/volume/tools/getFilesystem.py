"""
获取挂载点的文件系统类型
"""

from utils.confs import get_conf_manager


def get_filesystem(mount_point):
    """
    获取挂载点的文件系统类型
    
    Args:
        mount_point: 挂载点路径，格式取决于操作系统：
            - Linux: /mnt/disk1, /media/usb 等
            - Windows: C:\, D:\ 或挂载的目录
            - macOS: /Volumes/disk1, /mnt/disk1 等
    
    Returns:
        str: 文件系统类型，如果获取失败或不是挂载点则返回 None
        
        常见文件系统类型：
        - Linux: ext4, xfs, btrfs, ntfs, vfat, tmpfs, ltfs 等
        - Windows: NTFS, FAT32, exFAT, ReFS, ltfs 等
        - macOS: hfs, apfs, exfat, ntfs, ltfs 等
        
    注意：
        - 如果传入的是磁带机设备路径（如 /dev/st0, \\.\Tape0, /dev/tape0），
          且不是挂载点，函数会返回 'taptar'
        - 如果磁带机使用 LTFS（Linear Tape File System）挂载，会正常返回 'ltfs'
        - 如果磁带机通过 FUSE 等方式被挂载为文件系统，则可以正常获取
          文件系统类型（通常是 'fuse' 或对应的 FUSE 文件系统类型）
    """
    system = get_conf_manager().get("system")
    
    if system == "windows":
        from .windows.getFilesystem import get_filesystem as impl
    elif system == "linux":
        from .linux.getFilesystem import get_filesystem as impl
    elif system == "macos":
        from .macos.getFilesystem import get_filesystem as impl
    else:
        raise ValueError(f"不支持的系统: {system}")
    
    if impl is None:
        raise ValueError("获取平台对应的模块失败")
    
    return impl(mount_point)


__all__ = [
    "get_filesystem",
]

