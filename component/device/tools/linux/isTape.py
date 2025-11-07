import re


_TAPE_PATTERN = re.compile(r'^(/dev/)?st\d+$')


def is_tape(device: str) -> bool:
    """判断设备是否为磁带"""
    if not device:
        return False
    return _TAPE_PATTERN.match(device.strip()) is not None

