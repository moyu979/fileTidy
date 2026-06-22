from domain.storage.volume.enum import VolumeTypeMenu


def get_file_system(path: str) -> str:
    print(VolumeTypeMenu.prompt_text())
    while True:
        code = input(VolumeTypeMenu.input_hint()).strip()
        result = VolumeTypeMenu.from_code(code)
        if result is not None:
            return result
        print("无效输入，请按菜单输入对应编号。")
