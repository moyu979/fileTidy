import subprocess


def get_all_mount_points():
    result = subprocess.run(
        ["findmnt", "-rno", "TARGET,SOURCE"], capture_output=True, text=True
    )
    lines = result.stdout.strip().split("\n")
    mount_points = []
    # lines 是交替的：TARGET一行，SOURCE一行
    # 实际上findmnt -rno TARGET,SOURCE 会每行同时输出两列，不是分开两行的
    # 所以按空格分割即可
    for line in lines:
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            continue
        target, source = parts
        if source.startswith("/dev/sd"):
            mount_points.append(target)
    return mount_points


if __name__ == "__main__":
    mounts = get_physical_disk_mount_points()
    for m in mounts:
        print(m)
