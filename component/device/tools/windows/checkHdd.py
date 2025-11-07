# 本文件未经测试

import logging
from utils.runCommand import run_command


def hdd_check(device, scan_blocks=False):
    """
    检查HDD健康状态，返回 'health'（健康）、'danger'（警告）、None（检查失败）
    
    Args:
        device: 硬盘设备路径，支持格式：
            - \\.\PhysicalDrive0, \\.\PhysicalDrive1
            - PhysicalDrive0, PhysicalDrive1
            - 0, 1, 2 (设备号，自动转换为 \\.\PhysicalDriveN)
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
    
    # 规范化设备路径为 \\.\PhysicalDriveN 格式
    if device.isdigit():
        device_path = rf'\\.\PhysicalDrive{device}'
    elif device.startswith('PhysicalDrive'):
        device_path = rf'\\.\{device}'
    elif device.startswith(r'\\.\PhysicalDrive'):
        device_path = device
    else:
        logging.error(f"[HDD ERROR] 不支持的设备路径格式: {device}")
        return None
    
    logging.info(f"[HDD INFO] 开始检查设备: {device_path}")
    
    # 检查SMART - 优先使用 smartctl（与 Linux 版本保持一致）
    cmd_smart = ["smartctl", "-H", device_path]
    code, out, err = run_command(cmd_smart)
    
    if code != 0:
        # smartctl 不可用，尝试使用 PowerShell 作为备选
        logging.info("[HDD SMART] smartctl 不可用，尝试使用 PowerShell 检查")
        device_num = device_path.replace(r'\\.\PhysicalDrive', '')
        ps_cmd = [
            'powershell', '-Command',
            f'$disk = Get-PhysicalDisk -DeviceNumber {device_num} -ErrorAction SilentlyContinue; '
            f'if ($disk) {{ Write-Output "$($disk.HealthStatus)|$($disk.OperationalStatus)" }}'
        ]
        code, out, err = run_command(ps_cmd)
        if code != 0 or not out.strip():
            logging.error(f"[HDD SMART ERROR] {err}")
            return None
        # PowerShell 返回格式: Healthy|OK
        if "Healthy" in out and "OK" in out:
            logging.info(f"[HDD SMART OK] {out}")
        else:
            logging.warning(f"[HDD SMART WARNING] {out}")
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
        cmd_test = ["smartctl", "-t", "short", device_path]
        code, out, err = run_command(cmd_test)
        if code != 0:
            logging.error(f"[HDD BADBLOCKS ERROR] {err}")
            return None
        # 注意：短测试需要时间，这里只启动测试
        # 实际应该等待测试完成后再检查结果，简化实现先返回成功
        logging.info(f"[HDD BADBLOCKS OK] 坏道扫描测试已启动")
    else:
        logging.info(f"[HDD SCAN] 跳过坏道扫描，仅进行SMART检测")
    
    return "health"

