import os
from component.volume.volumeManager import volume_manager
from database.models import FileModel
from database.session import session_scope
from utils import get_hash


def reg_file(path):
    """
    注册目录下的所有文件到数据库中
    
    Args:
        path: 要注册的目录路径
    
    Raises:
        ValueError: 如果无法获取 volume_id
    """
    # 获取目录的 volume_id，如果不成功就报错
    volume_id = volume_manager.get_id(path, strict=False)
    if volume_id is None:
        raise ValueError(f"无法获取路径 {path} 的 volume_id")
    
    # 获取 volume_path
    volume_path = volume_manager.get_path(volume_id)
    if volume_path is None:
        raise ValueError(f"无法获取 volume_id {volume_id} 对应的路径")
    
    # 遍历所有文件，计算哈希值
    hash_list = get_hash(path)
    
    # 批量写入数据库
    with session_scope() as session:
        for file_path, file_hash in hash_list:
            # 计算相对路径
            if file_path.startswith(volume_path):
                relative_path = file_path.replace(volume_path, "", 1).lstrip(os.sep)
            else:
                relative_path = file_path
            
            file = FileModel(
                md5=file_hash,  # 1. md5
                size=os.path.getsize(file_path),  # 2. size - 文件大小（字节）
                add_time=str(int(os.path.getctime(file_path))),  # 3. add_time - 文件创建时间（时间戳字符串）
                from_path=relative_path, 
                now_path=relative_path, 
                now_volume=str(volume_id),
                now_name=os.path.basename(relative_path),  # 7. now_name - 文件名
                state="online",  # 8. state
                info="",  # 9. info
            )
            session.add(file)