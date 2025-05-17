# import logging
# import volume_manager.volumeFactory as volumeFactory
# import file_manager.files_manager as files_manager
# import init_setting.initSetting as initSetting
# logging.basicConfig(
#     level=logging.DEBUG,  # 设置日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 设置日志格式
#     #filename="app.log",  # 将日志写入文件（可选）
#     #filemode="a"  # 文件模式：'a' 表示追加，'w' 表示覆盖
# )
# initSetting.init_database()
# logging.info("init database")
# volumeFactory.VolumeFactory.load_exist_volumes()
# print(volumeFactory.VolumeFactory.no_init_volume)
# #volume=volumeFactory.VolumeFactory.load_volume(mount_point="referToDownloadVolumn")
# #volume=volumeFactory.VolumeFactory.load_upper_volume(path=None)
# #print(volume.to_json())
# #files_manager.Files.insert_files(file_path="./Transcode-X-scheduler")

import subprocess

def get_partition_capacity_bytes(partition):
    """
    获取指定分区的容量信息（以字节为单位）。
    :param partition: 分区名称（如 /dev/disk1s1）
    :return: 分区容量（整数，字节数），如 500068036608
    """
    try:
        # 调用 diskutil 命令
        result = subprocess.run(
            ["diskutil", "info", partition],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Error: {result.stderr.strip()}")

        # 解析输出，查找容量信息
        for line in result.stdout.splitlines():
            if "Disk Size" in line and "Bytes" in line:
                # 提取容量的字节数部分
                size_str = line.split("(")[1].split(" ")[0]  # 提取括号内的字节数
                return int(size_str)  # 转换为整数返回

    except Exception as e:
        print(f"获取分区容量时出错: {e}")
        return None

# 示例：获取 /dev/disk1s1 的容量（字节数）
if __name__ == "__main__":
    partition = "/dev/disk1s1"  # 替换为你的分区名称
    capacity_bytes = get_partition_capacity_bytes(partition)
    if capacity_bytes:
        print(f"分区 {partition} 的容量为: {capacity_bytes} 字节")
    else:
        print(f"无法获取分区 {partition} 的容量信息")