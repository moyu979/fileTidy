# 本文件未经测试

import logging
import os
from utils.runCommand import run_command


def ssd_check(device, scan_blocks=False):
    """
    检查SSD健康状态，返回 'health'（健康）、'danger'（警告）、None（检查失败）
    
    Args:
        device: SSD设备路径，支持格式：
            - /dev/disk0, /dev/disk1
            - disk0, disk1 (自动添加 /dev/ 前缀)
        scan_blocks: 是否开启坏道扫描，默认为False（SSD无需坏道扫描）
    
    Returns:
        str: 'health' 表示健康，'danger' 表示有警告
        None: 检查失败或发生错误
    """
    # 边界条件判断
    if device is None:
        logging.error("[SSD ERROR] 设备路径不能为None")
        return None
    
    if not isinstance(device, str) or device.strip() == "":
        logging.error("[SSD ERROR] 设备路径必须是有效的字符串")
        return None
    
    device = device.strip()
    
    # 规范化设备路径为 /dev/diskN 格式
    if device.startswith('/dev/disk'):
        device_path = device
    elif device.startswith('disk'):
        device_path = f'/dev/{device}'
    else:
        logging.error(f"[SSD ERROR] 不支持的设备路径格式: {device}")
        return None
    
    # 检查设备文件是否存在
    if not os.path.exists(device_path):
        logging.error(f"[SSD ERROR] 设备文件不存在: {device_path}")
        return None
    
    logging.info(f"[SSD INFO] 开始检查设备: {device_path}")
    
    # 检查SMART - 优先使用 smartctl（与 Linux 版本保持一致）
    cmd_smart = ["sudo", "smartctl", "-H", device_path]
    code, out, err = run_command(cmd_smart)
    
    if code != 0:
        # smartctl 不可用，尝试使用 diskutil 作为备选
        logging.info("[SSD SMART] smartctl 不可用，尝试使用 diskutil 检查")
        cmd_diskutil = ["diskutil", "info", device_path]
        code, out, err = run_command(cmd_diskutil)
        if code != 0:
            logging.error(f"[SSD SMART ERROR] {err}")
            return None
        # diskutil 输出中查找 SMART Status
        if "SMART Status" in out:
            if "Verified" in out:
                logging.info(f"[SSD SMART OK] {out}")
            else:
                logging.warning(f"[SSD SMART WARNING] {out}")
                return "danger"
        else:
            logging.warning("[SSD SMART] diskutil 无法获取 SMART 状态")
            return "danger"
    else:
        if "PASSED" not in out:
            logging.warning(f"[SSD SMART WARNING] {out}")
            return "danger"
        logging.info(f"[SSD SMART OK] {out}")
    
    # SSD 无需坏道扫描
    if scan_blocks:
        logging.info(f"[SSD SCAN] SSD 无需逐块扫描，跳过坏道检测")
    else:
        logging.info(f"[SSD SCAN] 跳过坏道扫描，仅进行SMART检测")
    
    return "health"

