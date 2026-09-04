# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 系统卷判断 - 检查路径是否为卷设备

from pathlib import Path


def is_volume(path: str) -> bool:
    """检查路径是否为合法的卷目录。

    合法条件：
      - 是目录
      - 仅包含 datas/ 和 meta/ 两个子目录
      - meta/ 下恰好有一个文件（作为卷序列号）
    """
    p = Path(path)
    if not p.is_dir():
        return False
    subdir_names = [entry.name for entry in p.iterdir() if entry.is_dir()]
    if not (len(subdir_names) == 2 and set(subdir_names) == {"meta", "datas"}):
        return False
    meta_files = [f for f in (p / "meta").iterdir() if f.is_file()]
    return len(meta_files) == 1

