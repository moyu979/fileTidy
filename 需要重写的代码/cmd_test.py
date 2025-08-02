import subprocess


def get_partition_capacity(partition):
    """
    获取指定分区的容量信息。
    :param partition: 分区名称（如 /dev/disk1s1）
    :return: 分区容量（字符串），如 '500GB'
    """
    try:
        # 调用 diskutil 命令
        result = subprocess.run(
            ["diskutil", "info", partition],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Error: {result.stderr.strip()}")

        # 解析输出，查找容量信息
        for line in result.stdout.splitlines():
            if "Disk Size" in line:
                # 提取容量信息
                return line.split(":")[1].strip()

    except Exception as e:
        print(f"获取分区容量时出错: {e}")
        return None


# 示例：获取 /dev/disk1s1 的容量
if __name__ == "__main__":
    partition = "/dev/disk1s1"  # 替换为你的分区名称
    capacity = get_partition_capacity(partition)
    if capacity:
        print(f"分区 {partition} 的容量为: {capacity}")
    else:
        print(f"无法获取分区 {partition} 的容量信息")
