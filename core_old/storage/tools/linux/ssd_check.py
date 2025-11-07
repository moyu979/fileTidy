# 本文件未经测试
import subprocess
import logging
import os


def run_command(cmd):
    """同步运行一个命令，并返回输出结果"""
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    return result.returncode, result.stdout.decode(errors='ignore'), result.stderr.decode(errors='ignore')


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
    logging.warning("[AI WARNING] 这些文件是由AI生成的，还未经过测试")
    
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
    
    # 检查SMART状态
    cmd_smart = ["sudo", "smartctl", "-H", device]
    code, out, err = run_command(cmd_smart)
    if code != 0:
        logging.error(f"[SSD SMART ERROR] {err}")
        return None
    
    logging.info(f"[SSD SMART STATUS] {out}")
    
    # 判断SMART状态
    if "PASSED" in out:
        smart_status = "health"
        logging.info("[SSD SMART OK] SMART检查通过")
    elif "FAILED" in out or "WARNING" in out or "Pre-fail" in out:
        smart_status = "danger"
        logging.warning(f"[SSD SMART WARNING] SMART检查失败或警告: {out}")
    else:
        smart_status = "danger"
        logging.warning(f"[SSD SMART WARNING] 未知SMART状态: {out}")
    
    if scan_blocks:
        logging.info(f"ssd的健康扫描无需逐块读取")
    
    return smart_status

if __name__ == "__main__":
    print(ssd_check("/dev/sda"))