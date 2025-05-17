import subprocess

def get_partition_capacity_bytes(partition):
    """
    获取指定分区的容量信息（以字节为单位）。
    :param partition: 分区名称（如 /dev/disk1s1）
    :return: 分区容量（整数，字节数），如 500068036608
    """
    try:
        if partition.startswith("/dev/"):
            pass
        else:
            partition = "/dev/" + partition

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