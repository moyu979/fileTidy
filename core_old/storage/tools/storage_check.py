# 本文件未经测试
import logging
from core.conf import conf

# 警告：这些文件是由AI生成的，还未经过测试


def tape_check(storage):
    system = conf.get("platform")
    device_path = getattr(storage, "device_path", None)
    if not device_path:
        logging.error("[TAPE CHECK] storage.device_path 未设置，无法进行健康检查")
        return "error"
    if system and system.lower() == "linux":
        from core.storage.tools.linux.tape_check import tape_check as linux_tape_check

        return linux_tape_check(device_path)
    else:
        logging.error(f"[TAPE CHECK] 当前系统({system})不支持磁带健康检查")
        return "error"


def hdd_check(storage):
    system = conf.get("platform")
    device_path = getattr(storage, "device_path", None)
    if not device_path:
        logging.error("[HDD CHECK] storage.device_path 未设置，无法进行健康检查")
        return "error"
    if system and system.lower() == "linux":
        from core.storage.tools.linux.hdd_check import hdd_check as linux_hdd_check

        return linux_hdd_check(device_path)
    else:
        logging.error(f"[HDD CHECK] 当前系统({system})不支持HDD健康检查")
        return "error"


def ssd_check(storage):
    system = conf.get("platform")
    device_path = getattr(storage, "device_path", None)
    if not device_path:
        logging.error("[SSD CHECK] storage.device_path 未设置，无法进行健康检查")
        return "error"
    if system and system.lower() == "linux":
        from core.storage.tools.linux.ssd_check import ssd_check as linux_ssd_check

        return linux_ssd_check(device_path)
    else:
        logging.error(f"[SSD CHECK] 当前系统({system})不支持SSD健康检查")
        return "error"
