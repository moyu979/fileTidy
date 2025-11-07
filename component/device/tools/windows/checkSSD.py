# 本文件未经测试

import logging
from utils.runCommand import run_command


def ssd_check(device, scan_blocks=False):
    """
    检查SSD健康状态，返回 'health'（健康）、'danger'（警告）、None（检查失败）
    
    Args:
        device: SSD设备路径，支持格式：
            - \\.\PhysicalDrive0, \\.\PhysicalDrive1
            - PhysicalDrive0, PhysicalDrive1
            - 0, 1, 2 (设备号，自动转换为 \\.\PhysicalDriveN)
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
    
    # 规范化设备路径为 \\.\PhysicalDriveN 格式
    if device.isdigit():
        device_path = rf'\\.\PhysicalDrive{device}'
    elif device.startswith('PhysicalDrive'):
        device_path = rf'\\.\{device}'
    elif device.startswith(r'\\.\PhysicalDrive'):
        device_path = device
    else:
        logging.error(f"[SSD ERROR] 不支持的设备路径格式: {device}")
        return None
    
    logging.info(f"[SSD INFO] 开始检查设备: {device_path}")
    
    # 检查SMART - 优先使用 smartctl（与 Linux 版本保持一致）
    cmd_smart = ["smartctl", "-H", device_path]
    code, out, err = run_command(cmd_smart)
    
    if code != 0:
        # smartctl 不可用，尝试使用 PowerShell 作为备选
        logging.info("[SSD SMART] smartctl 不可用，尝试使用 PowerShell 检查")
        device_num = device_path.replace(r'\\.\PhysicalDrive', '')
        ps_cmd = [
            'powershell', '-Command',
            f'$disk = Get-PhysicalDisk -DeviceNumber {device_num} -ErrorAction SilentlyContinue; '
            f'if ($disk) {{ Write-Output "$($disk.HealthStatus)|$($disk.OperationalStatus)" }}'
        ]
        code, out, err = run_command(ps_cmd)
        if code != 0 or not out.strip():
            logging.error(f"[SSD SMART ERROR] {err}")
            return None
        # PowerShell 返回格式: Healthy|OK
        if "Healthy" in out and "OK" in out:
            logging.info(f"[SSD SMART OK] {out}")
        else:
            logging.warning(f"[SSD SMART WARNING] {out}")
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

