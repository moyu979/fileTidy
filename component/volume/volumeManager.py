"""
设备管理器，用于管理设备实例
"""

from component.device.deviceFactory import DeviceFactory
from component.volume.volumeFactory import VolumeFactory
import os
import re
import shutil
from component.volume.tools.isMountPoint import is_mount_point
from component.volume.volumeFactory import VolumeFactory
from database.session import session_scope
from utils.idGenerater import generate_id
from apis.regFile import reg_file

class VolumeManager:
    """设备管理器，管理设备实例"""
    
    def __init__(self):
        self.devices = []
    

    def regVolume(self, volume_path, volume_id=None):
        """
        登记一个新卷
        
        Args:
            volume_path: 卷路径（必须是挂载点）
            volume_id: 可选的卷ID，如果 info/id_xxx 文件存在，则必须与文件中的ID相同或为None
        
        Returns:
            Volume: 创建的卷实例，如果失败返回 None
        """
        
        
        if not volume_path:
            return None
        
        # 规范化路径
        normalized_path = os.path.abspath(os.path.expanduser(volume_path))
        normalized_path = os.path.normpath(normalized_path)
        
        # 约束：volume_path 一定要是挂载点
        if not is_mount_point(normalized_path):
            return None
        
        # 检查 info 目录和 id 文件
        info_dir = os.path.join(normalized_path, "info")
        id_file_pattern = r'^id_(\d+)$'  # id_xxx 格式
        
        extracted_id = None
        if os.path.isdir(info_dir):
            # 查找 id_xxx 文件
            try:
                for filename in os.listdir(info_dir):
                    match = re.match(id_file_pattern, filename)
                    if match:
                        extracted_id = match.group(1)
                        break
            except (OSError, IOError):
                pass
        
        # 确定使用的 volume_id
        if extracted_id is not None:
            # 如果存在 id 文件，volume_id 参数只能为 None 或与序列号相同
            if volume_id is not None and str(volume_id) != extracted_id:
                return None  # 参数不匹配
            final_volume_id = extracted_id
        else:
            # 如果不存在 id 文件
            if volume_id is not None:
                final_volume_id = str(volume_id)
            else:
                # 随机生成一个数字ID
                import random
                final_volume_id = str(random.randint(1, 999999999))  # 生成一个随机数字ID
        
        # 调用 volumeFactory.createVolume 创建卷
        volume = VolumeFactory.createVolume(normalized_path, final_volume_id)
        if volume is None:
            return None
        
        # 设置 volume_id 到 VolumeModel（id 是 Integer 类型）
        try:
            volume.orm_model.id = int(final_volume_id)
        except ValueError:
            # 如果无法转换为整数，使用默认值或生成新的数字ID
            from utils.idGenerater import generate_numeric_id
            volume.orm_model.id = generate_numeric_id() % 2147483647  # SQLite Integer 的最大值
            final_volume_id = str(volume.orm_model.id)
        
        volume.orm_model.name = final_volume_id
        
        # 写入数据库
        with session_scope() as session:
            session.add(volume.orm_model)
        
        # 检查并构建文件结构：应该有 datas 和 info 两个文件夹
        datas_dir = os.path.join(normalized_path, "datas")
        info_dir = os.path.join(normalized_path, "info")
        
        # 如果 info 目录不存在，创建它
        if not os.path.isdir(info_dir):
            os.makedirs(info_dir, exist_ok=True)
        
        # 创建 id 文件（如果不存在）
        id_file_path = os.path.join(info_dir, f"id_{final_volume_id}")
        if not os.path.exists(id_file_path):
            with open(id_file_path, 'w') as f:
                f.write(final_volume_id)
        
        # 检查是否需要重构文件结构
        needs_reorganize = False
        if not os.path.isdir(datas_dir):
            needs_reorganize = True
        else:
            # 检查是否有文件/目录在根目录下（除了 datas 和 info）
            for item in os.listdir(normalized_path):
                item_path = os.path.join(normalized_path, item)
                if item not in ['datas', 'info'] and (os.path.isfile(item_path) or os.path.isdir(item_path)):
                    needs_reorganize = True
                    break
        
        # 如果需要重构，将所有数据移动到 datas 中
        if needs_reorganize:
            # 创建 datas 目录
            if not os.path.isdir(datas_dir):
                os.makedirs(datas_dir, exist_ok=True)
            
            # 移动所有文件和目录到 datas（除了 datas 和 info）
            for item in os.listdir(normalized_path):
                if item in ['datas', 'info']:
                    continue
                
                item_path = os.path.join(normalized_path, item)
                target_path = os.path.join(datas_dir, item)
                
                try:
                    if os.path.exists(target_path):
                        # 如果目标已存在，可能需要处理冲突
                        continue
                    shutil.move(item_path, target_path)
                except (OSError, IOError) as e:
                    # 移动失败，记录错误但继续
                    print(f"移动 {item_path} 到 {target_path} 失败: {e}")
        
        # 调用 reg_file 进行文件登记（登记 datas 目录）
        try:
            reg_file(datas_dir)
        except Exception as e:
            # 登记失败，但不影响卷的创建
            print(f"登记文件失败: {e}")
        
        return volume

    def exists_in_database(self, volume_path=None, name=None):
        """
        检查给定的卷是否存在，如果存在，返回True，否则返回False
        
        Args:
            volume_path: 卷路径（对应 unique_mount_point）
            name: 卷名称
            两者必须至少提供一个，不能同时提供
        """
        if not volume_path and not name:
            raise ValueError("必须提供 volume_path 或 name 至少一个")
        
        if volume_path and name:
            raise ValueError("不能同时提供 volume_path 和 name")
        
        # 统一用 name 查数据库
        from database.models import VolumeModel
        
        # 如果传入的是路径，通过 unique_mount_point 查询
        if volume_path:
            volume = VolumeModel.query.filter(VolumeModel.unique_mount_point == volume_path).first()
            return volume is not None
        
        # 如果传入的是 name，直接用 name 查询
        volume = VolumeModel.query.filter(VolumeModel.name == name).first()
        return volume is not None

    def get_path(self, device_path):
        """
        获取设备路径，如果卷存在但没挂载，返回None
        """
        pass

    def get_volume(self, volume_path, strict=False):
        """
        获取卷id和路径
        
        Args:
            volume_path: 要检查的路径
            strict: 
                为False时，会向上检查目录树，获得最近的卷id和路径
                为True时，会严格要求给出的路径就是卷的挂载路径（是挂载点且有info/id文件）
        
        Returns:
            tuple: (volume_id, volume_path) 如果找到，否则返回 (None, None)
        """
        from component.volume.tools.getUpperVolume import get_upper_volume
        from component.volume.tools.isMountPoint import is_mount_point
        import os
        import re
        
        if not volume_path:
            return None, None
        
        # 非严格模式：向上遍历查找
        if not strict:
            volume_path_result, volume_id = get_upper_volume(volume_path)
            return volume_id, volume_path_result
        
        # 严格模式：只检查当前目录是否是 volume 根
        try:
            # 规范化路径
            current_path = os.path.abspath(os.path.expanduser(volume_path))
            
            # 如果是文件，检查其所在目录
            if os.path.isfile(current_path):
                current_path = os.path.dirname(current_path)
            
            # 检查是否是挂载点
            if not is_mount_point(current_path):
                return None, None
            
            # 检查是否有 info 子目录
            info_dir = os.path.join(current_path, "info")
            if not os.path.isdir(info_dir):
                return None, None
            
            # 遍历 info 目录中的文件，查找 id 文件
            try:
                for filename in os.listdir(info_dir):
                    # 检查文件名格式：id + 任意位数字
                    match = re.match(r'^id(\d+)$', filename)
                    if match:
                        volume_id = match.group(1)
                        return volume_id, current_path
            except (OSError, IOError):
                return None, None
            
            return None, None
        except (OSError, IOError):
            return None, None

    def checkVolume(self, volume_path):
        """
        检查卷的介质情况
        """
        volume=VolumeFactory.getVolume(volume_path)
        volume.check()

    

# 模块级单例实例
volume_manager = VolumeManager()

