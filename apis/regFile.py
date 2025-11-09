from hashlib import md5
import os
from component.volume import volume
from component.volume.volumeManager import volume_manager
from database.models import FileModel
from database.session import session_scope
from utils import get_hash

def regFiles(path):
    """
    注册一个文件到数据库中
    会自动检查文件的MD5值，如果文件不存在，则创建一个新文件
    如果文件存在，还没完成
    """
    volume_id = volume_manager.get_id(path,strict=False)
    if volume_id is None:
        #如果不存在volumeid，使用默认的
        volume_id = 0

    volume_path = volume_manager.get_path(volume_id)
    hash_list = get_hash(path)
    for path,hash in hash_list:
        size=os.path.getsize(path)
        from_path = path.replace(volume_path,"")
        add_time = os.path.getctime(path)
        now_path = from_path
        now_name = os.path.basename(now_path)
        now_volume = volume_id
        file=FileModel(
            md5=hash,
            size=size,
            add_time=add_time,
            from_path=from_path,
            now_path=from_path,
            now_volume=now_volume,
            now_name=now_name,
            state="online",
            info="",
            )
        with session_scope() as session:
            session.add(file)