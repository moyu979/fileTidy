from pathlib import Path


def is_volume(path: str) -> bool:
    p = Path(path)
    if not p.is_dir():
        return False
    subdir_names = [entry.name for entry in p.iterdir() if entry.is_dir()]
    return len(subdir_names) == 2 and set(subdir_names) == {"meta", "datas"}

