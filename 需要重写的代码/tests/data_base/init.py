import os
import sys

current_file = os.path.abspath(__file__)

# 获取它的上两层目录
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
print(parent_dir)
# 添加到 sys.path（如果尚未添加）
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from database.init_database import init_database

if __name__ == "__main__":
    init_database()
