# 本文件未经测试
import logging
import os
from utils.runCommand import run_command


def ssd_check(device, scan_blocks=False):
    """
    检查SSD健康状态，返回 'health'（健康）、'danger'（警告）、None（检查失败）
    
    Args:
        device: SSD设备路径，默认为 /dev/sda
        scan_blocks: 是否开启坏道扫描，默认为False（只进行SMART检测）
    
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
    
    # 检查设备文件是否存在
    if not os.path.exists(device):
        logging.error(f"[SSD ERROR] 设备文件不存在: {device}")
        return None
    
    # 检查是否为块设备
    if not os.path.exists(f"/sys/block/{os.path.basename(device)}"):
        logging.error(f"[SSD ERROR] 不是有效的块设备: {device}")
        return None
    
    logging.info(f"[SSD INFO] 开始检查设备: {device}")
    
    # 检查SMART
    cmd_smart = ["sudo", "smartctl", "-H", device]
    code, out, err = run_command(cmd_smart)
    if code != 0:
        logging.error(f"[SSD SMART ERROR] {err}")
        return None
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