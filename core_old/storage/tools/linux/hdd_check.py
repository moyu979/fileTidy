import subprocess
import logging
import os


def run_command(cmd):
    """同步运行一个命令，并返回输出结果"""
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode, result.stdout.decode(), result.stderr.decode()


def hdd_check(device, scan_blocks=False):
    """
    检查HDD健康状态，返回 'health'（健康）、'danger'（警告）、None（检查失败）
    
    Args:
        device: 硬盘设备路径，默认为 /dev/sda
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
    
    # 检查设备文件是否存在
    if not os.path.exists(device):
        logging.error(f"[HDD ERROR] 设备文件不存在: {device}")
        return None
    
    # 检查是否为块设备
    if not os.path.exists(f"/sys/block/{os.path.basename(device)}"):
        logging.error(f"[HDD ERROR] 不是有效的块设备: {device}")
        return None
    
    logging.info(f"[HDD INFO] 开始检查设备: {device}")
    
    # 检查SMART
    cmd_smart = ["sudo", "smartctl", "-H", device]
    code, out, err = run_command(cmd_smart)
    if code != 0:
        logging.error(f"[HDD SMART ERROR] {err}")
        return None
    if "PASSED" not in out:
        logging.warning(f"[HDD SMART WARNING] {out}")
        return "danger"
    logging.info(f"[HDD SMART OK] {out}")
    
    # 如果开启扫描，则进行坏道检测
    if scan_blocks:
        logging.info(f"[HDD SCAN] 开始坏道扫描，设备: {device}")
        # 使用-n参数进行非破坏性读取测试，-s显示进度，-v详细输出
        cmd_badblocks = ["sudo", "badblocks", "-n", "-sv", device]
        code, out, err = run_command(cmd_badblocks)
        if code != 0:
            logging.error(f"[HDD BADBLOCKS ERROR] {err}")
            return None
        if out.strip():
            logging.warning(f"[HDD BADBLOCKS WARNING] 发现坏道: {out}")
            return "danger"
        logging.info(f"[HDD BADBLOCKS OK] 坏道扫描完成，未发现坏道")
    else:
        logging.info(f"[HDD SCAN] 跳过坏道扫描，仅进行SMART检测")
    
    return "health"
