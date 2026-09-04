# CHECK: 待检查 - 系统文件系统检测 - 识别卷的文件系统类型

from domain.storage.volume.enum import VolumeTypeMenu


def get_file_system(path: str) -> str:
    """
    获取指定路径对应的文件系统类型（占位实现：通过菜单由用户手动选择）。

    Args:
        path: 卷路径

    Returns:
        文件系统类型字符串
    """
    # MANUAL: 这是占位实现，需要替换为真正的文件系统检测（如 df -T / blkid）
    print(VolumeTypeMenu.prompt_text())
    while True:
        code = input(VolumeTypeMenu.input_hint()).strip()
        result = VolumeTypeMenu.from_code(code)
        if result is not None:
            return result
        print("无效输入，请按菜单输入对应编号。")
