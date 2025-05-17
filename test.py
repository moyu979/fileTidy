import logging
import volume_manager.volumeFactory as volumeFactory
import file_manager.files_manager as files_manager
import init_setting.initSetting as initSetting
logging.basicConfig(
    level=logging.DEBUG,  # 设置日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 设置日志格式
    #filename="app.log",  # 将日志写入文件（可选）
    #filemode="a"  # 文件模式：'a' 表示追加，'w' 表示覆盖
)
initSetting.init_database()
logging.info("init database")
#volume=volumeFactory.VolumeFactory.load_volume(mount_point="referToDownloadVolumn")
#volume=volumeFactory.VolumeFactory.load_upper_volume(path=None)
#print(volume.to_json())
files_manager.Files.insert_files(file_path="C:\\Users\\30278\\Desktop\\test")

