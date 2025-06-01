import volume_manager.volumeFactory as vf
from volume_manager.volume import Volume
from file_manager.file import File
import volume_manager.volume as v
import logging 

from init_setting.initSetting import init_database
logging.basicConfig(
    level=logging.DEBUG,  # 设置日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 设置日志格式
    #filename="app.log",  # 将日志写入文件（可选）
    #filemode="a"  # 文件模式：'a' 表示追加，'w' 表示覆盖
)
init_database()

vf.VolumeFactory.load_volume_from_database(mount_point="H:\\")
print(vf.VolumeFactory.get_volume("0").to_json())

vf.VolumeFactory.show_all_volumes()
file_path="H:\\datas\\cmd.bat"
f=File()
f.abspath=file_path
f.auto_complete()
f.append_to_database()
print(f)