import os
import sys

current_file = os.path.abspath(__file__)

# 获取它的上两层目录
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
# 添加到 sys.path（如果尚未添加）
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import core.storage.storageFactory as sf

sf.StorageFactory.load_all_storage()
sf.StorageFactory.set_value("VB02a7bd3e-ac1f1517", "name", "asdf")
