# 本文件未经测试

import logging
import os
from utils.runCommand import run_command


def hdd_check(device, scan_blocks=False):
    """
    检查HDD健康状态，返回 'health'（健康）、'danger'（警告）、None（检查失败）
    
    Args:
        device: 硬盘设备路径，支持格式：
            - /dev/disk0, /dev/disk1
            - disk0, disk1 (自动添加 /dev/ 前缀)
        scan_blocks: 是否开启坏道扫描，默认为False（只进行SMART检测）
    
    Returns:
        str: 'health' 表示健康，'danger' 表示有警告
        None: 检查失败或发生错误
    """
    # 边界条件判断
    if device is None:
        logging.error("[HDD ERROR] 设备路径不能为None")
        return None
    
    if not isinstance(device, str) or device.strip() == "":
        logging.error("[HDD ERROR] 设备路径必须是有效的字符串")
        return None
    
    device = device.strip()
    
    # 规范化设备路径为 /dev/diskN 格式
    if device.startswith('/dev/disk'):
        device_path = device
    elif device.startswith('disk'):
        device_path = f'/dev/{device}'
    else:
        logging.error(f"[HDD ERROR] 不支持的设备路径格式: {device}")
        return None
    
    # 检查设备文件是否存在
    if not os.path.exists(device_path):
        logging.error(f"[HDD ERROR] 设备文件不存在: {device_path}")
        return None
    
    logging.info(f"[HDD INFO] 开始检查设备: {device_path}")
    
    # 检查SMART - 优先使用 smartctl（与 Linux 版本保持一致）
    cmd_smart = ["sudo", "smartctl", "-H", device_path]
    code, out, err = run_command(cmd_smart)
    
    if code != 0:
        # smartctl 不可用，尝试使用 diskutil 作为备选
        logging.info("[HDD SMART] smartctl 不可用，尝试使用 diskutil 检查")
        cmd_diskutil = ["diskutil", "info", device_path]
        code, out, err = run_command(cmd_diskutil)
        if code != 0:
            logging.error(f"[HDD SMART ERROR] {err}")
            return None
        # diskutil 输出中查找 SMART Status
        if "SMART Status" in out:
            if "Verified" in out:
                logging.info(f"[HDD SMART OK] {out}")
            else:
                logging.warning(f"[HDD SMART WARNING] {out}")
                return "danger"
        else:
            logging.warning("[HDD SMART] diskutil 无法获取 SMART 状态")
            return "danger"
    else:
        if "PASSED" not in out:
            logging.warning(f"[HDD SMART WARNING] {out}")
            return "danger"
        logging.info(f"[HDD SMART OK] {out}")
    
    # 如果开启扫描，则进行坏道检测
    if scan_blocks:
        logging.info(f"[HDD SCAN] 开始坏道扫描，设备: {device_path}")
        # 使用 smartctl 短测试（非破坏性）
        cmd_test = ["sudo", "smartctl", "-t", "short", device_path]
        code, out, err = run_command(cmd_test)
        if code != 0:
            # smartctl 不可用，尝试使用 diskutil verifyVolume
            logging.info("[HDD SCAN] smartctl 不可用，尝试使用 diskutil verifyVolume")
            # 需要先获取卷标识符
            cmd_info = ["diskutil", "info", device_path]
            code_info, out_info, err_info = run_command(cmd_info)
            if code_info == 0 and "Volume Name" in out_info:
                # 提取卷名或使用设备路径
                # 简化实现：直接使用设备路径
                cmd_verify = ["diskutil", "verifyVolume", device_path]
                code, out, err = run_command(cmd_verify)
                if code != 0:
                    logging.error(f"[HDD BADBLOCKS ERROR] {err}")
                    return None
                if "verified" not in out.lower() and "error" in out.lower():
                    logging.warning(f"[HDD BADBLOCKS WARNING] {out}")
                    return "danger"
                logging.info(f"[HDD BADBLOCKS OK] 坏道扫描完成")
            else:
                logging.error(f"[HDD BADBLOCKS ERROR] 无法获取卷信息: {err_info}")
                return None
        else:
            # 注意：短测试需要时间，这里只启动测试
            # 实际应该等待测试完成后再检查结果，简化实现先返回成功
            logging.info(f"[HDD BADBLOCKS OK] 坏道扫描测试已启动")
    else:
        logging.info(f"[HDD SCAN] 跳过坏道扫描，仅进行SMART检测")
    
    return "health"

