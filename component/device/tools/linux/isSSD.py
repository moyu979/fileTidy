import os


def is_ssd(device: str) -> bool:
    """判断设备是否为SSD"""
    if not device:
        return False
    device_name = os.path.basename(device)
    rotational_file = f"/sys/block/{device_name}/queue/rotational"
    if os.path.exists(rotational_file):
        with open(rotational_file, 'r') as f:
            return f.read().strip() == "0"
    return False

