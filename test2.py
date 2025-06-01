import volume_manager.volume as v
import logging 
logging.basicConfig(
    level=logging.DEBUG,  # 设置日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 设置日志格式
    #filename="app.log",  # 将日志写入文件（可选）
    #filemode="a"  # 文件模式：'a' 表示追加，'w' 表示覆盖
)
path=input("请输入挂载点")
vol=v.Volume(mount_point=path)
print(vol.to_json())
vol.file_detector()
