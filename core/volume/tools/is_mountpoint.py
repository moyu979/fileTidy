import os

def is_mountpoint(path: str) -> bool:
    """
    判断某路径是否为独立挂载点（卷），支持Linux和Windows
    Args:
        path: 路径字符串
    Returns:
        True: 是挂载点
        False: 不是挂载点
    """
    return os.path.ismount(path)

if __name__ == "__main__":
    print(is_mountpoint("/ssa"))
