"""
卷工厂，用于创建和管理卷实例,同时提供对外接口
"""

import os
from datetime import datetime
from component.volume.volume import Volume
from component.volume.tools.getCapacity import get_capacity
from component.volume.tools.getFilesystem import get_filesystem
from component.volume.tools.isMountPoint import is_mount_point
from database.models import VolumeModel


class VolumeFactory:
    """卷工厂，提供静态方法创建卷实例"""
    
    @staticmethod
    def createVolume(volume_path,volume_id=None):
        """
        根据卷路径创建对应的卷实例，用于新建卷时使用
        
        Args:
            volume_path: 卷路径（挂载点）
            
        Returns:
            卷实例（Volume），如果无法识别卷则返回 None
        """
        if not volume_path:
            return None
        
        # 规范化挂载点路径
        normalized_path = os.path.abspath(os.path.expanduser(volume_path))
        normalized_path = os.path.normpath(normalized_path)
        
        # 检查是否是挂载点
        if not is_mount_point(normalized_path):
            return None
        
        # 创建 VolumeModel
        VolumeORM = VolumeModel(
            name = "",
            kind = "",
            add_time = datetime.utcnow(),
            last_check_time = None,
            capacity = get_capacity(normalized_path),
            info = "",
            unique_mount_point = normalized_path,
            file_system = get_filesystem(normalized_path)
        )
        
        # 根据文件系统类型设置 kind（可选，可以根据需要调整）
        if VolumeORM.file_system:
            VolumeORM.kind = VolumeORM.file_system.upper()
        else:
            VolumeORM.kind = "Unknown"
        
        return Volume(orm_model=VolumeORM, volume_path=normalized_path)

    @staticmethod
    def getVolume(volume_path):
        """
        根据卷路径获取对应的卷实例，用于获取已经记录的卷
        
        Args:
            volume_path: 卷路径（挂载点）
            
        Returns:
            卷实例（Volume），如果找不到则返回 None
        """
        if not volume_path:
            return None
        
        # 规范化挂载点路径
        normalized_path = os.path.abspath(os.path.expanduser(volume_path))
        normalized_path = os.path.normpath(normalized_path)
        
        # 通过 unique_mount_point 查找
        volume = VolumeModel.query.filter(VolumeModel.unique_mount_point == normalized_path).first()
        if volume:
            return Volume(orm_model=volume, volume_path=normalized_path)
        else:
            return None

