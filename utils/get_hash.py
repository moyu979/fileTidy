import hashlib
import os

from utils.confs.manager import get_conf_manager


def _hash_file(path: str) -> str:
    chunk_size = int(get_conf_manager().get("hash_check_memery")) * 1024 * 1024
    hasher = hashlib.md5()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_hash(path: str):
    if os.path.isfile(path):
        return [[path, _hash_file(path)]]
    if os.path.isdir(path):
        result = []
        for root, _, files in os.walk(path):
            for name in files:
                file_path = os.path.join(root, name)
                result.append([file_path, _hash_file(file_path)])
        return result
    raise FileNotFoundError(path)

