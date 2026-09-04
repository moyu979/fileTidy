# CHECK: 待检查 - 系统路径判断 - 检查路径是否为指定类型

"""
判断给定的字符串是否是一个文件系统路径。
支持 macOS (Darwin)、Linux、Windows 平台自动检测，
其他平台则回退到手动输入。
"""

import os
import re
import sys


def _is_path_darwin(input_str: str) -> bool:
    """
    判断输入字符串是否为 macOS 平台的有效路径。

    Args:
        input_str: 待判断的字符串

    Returns:
        是有效路径返回 True，否则返回 False
    """
    # 空字符串不是路径
    if not input_str:
        return False
    # 以 ~ 开头（家目录简写）
    if input_str.startswith("~"):
        return True
    # 以 / 开头的绝对路径
    if input_str.startswith("/"):
        return True
    # 相对路径：包含 / 或 ./
    if input_str.startswith("./") or input_str.startswith("../"):
        return True
    if "/" in input_str:
        return True
    # 如果路径已存在，肯定是路径
    if os.path.exists(input_str):
        return True
    return False


def _is_path_linux(input_str: str) -> bool:
    """
    判断输入字符串是否为 Linux 平台的有效路径。

    Args:
        input_str: 待判断的字符串

    Returns:
        是有效路径返回 True，否则返回 False
    """
    if not input_str:
        return False
    if input_str.startswith("~"):
        return True
    if input_str.startswith("/"):
        return True
    if input_str.startswith("./") or input_str.startswith("../"):
        return True
    if "/" in input_str:
        return True
    if os.path.exists(input_str):
        return True
    return False


def _is_path_windows(input_str: str) -> bool:
    """
    判断输入字符串是否为 Windows 平台的有效路径。

    支持驱动器字母（C:\）、UNC 路径（\\server\share）等格式。

    Args:
        input_str: 待判断的字符串

    Returns:
        是有效路径返回 True，否则返回 False
    """
    if not input_str:
        return False
    # 驱动器字母开头: C:\ D:\ 等（不区分大小写）
    if re.match(r"^[A-Za-z]:[\\/]", input_str):
        return True
    # UNC 路径: \\server\share
    if input_str.startswith("\\\\"):
        return True
    # 以 ./ ../ 开头
    if input_str.startswith(".\\") or input_str.startswith("..\\"):
        return True
    if input_str.startswith("./") or input_str.startswith("../"):
        return True
    # 包含 \ 或 /
    if "\\" in input_str or "/" in input_str:
        return True
    # 如果路径已存在
    if os.path.exists(input_str):
        return True
    return False


def _is_path_manual(input_str: str) -> bool:
    """
    回退到手动输入：由用户交互式判断字符串是否为路径。

    Args:
        input_str: 待判断的字符串

    Returns:
        用户确认是路径返回 True，否则返回 False
    """
    data = input(
        f"判定字符串是否是路径的功能还没写，请手动判定「{input_str}」是否是一个路径\n（y/n）"
    )
    return data.strip().lower() in ("y", "yes")


def is_path(input_str: str) -> bool:
    """判断 input_str 是否是一个文件系统路径。

    根据当前运行平台自动选择判定策略：
    - darwin / linux：Unix 风格路径
    - win32：Windows 风格路径（含驱动器字母和 UNC）
    - 其他：回退到手动输入确认
    """
    platform = sys.platform

    if platform == "darwin":
        return _is_path_darwin(input_str)
    elif platform == "linux":
        return _is_path_linux(input_str)
    elif platform == "win32":
        return _is_path_windows(input_str)
    else:
        return _is_path_manual(input_str)