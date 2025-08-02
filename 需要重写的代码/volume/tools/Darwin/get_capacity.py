import subprocess


def get_mount_point_capacity(mount_point):
    """
    获取指定挂载点的容量信息（以字节为单位）。
    :param mount_point: 挂载点路径（如 /Volumes/MyDisk）
    :return: 总容量、已用容量、可用容量（单位：字节）
    """
    try:
        # 调用 df 命令
        result = subprocess.run(
            ["df", "-k", mount_point],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Error: {result.stderr.strip()}")

        # 解析 df 输出
        lines = result.stdout.splitlines()
        if len(lines) < 2:
            raise RuntimeError("无法解析 df 输出")

        # 第二行包含容量信息
        data = lines[1].split()
        total = int(data[1]) * 1024  # 总容量（块大小为 1K，转换为字节）
        used = int(data[2]) * 1024  # 已用容量
        available = int(data[3]) * 1024  # 可用容量

        return total, used, available

    except Exception as e:
        print(f"获取挂载点容量时出错: {e}")
        return None, None, None


# 示例：获取 /Volumes/MyDisk 的容量
if __name__ == "__main__":
    mount_point = "/Volumes/MyDisk"  # 替换为你的挂载点路径
    total, used, available = get_mount_point_capacity(mount_point)
    if total is not None:
        print(f"挂载点 {mount_point} 的容量信息：")
        print(f"总容量: {total} 字节")
        print(f"已用容量: {used} 字节")
        print(f"可用容量: {available} 字节")
    else:
        print(f"无法获取挂载点 {mount_point} 的容量信息")
