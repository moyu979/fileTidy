import subprocess
import logging

# 警告：这些文件是由AI生成的，还未经过测试


def ssd_check(device="/dev/sda"):
    """
    检查SSD健康状态，返回 'health'（健康）、'danger'（警告）、'error'（命令失败）
    """
    logging.warning("[AI WARNING] 这些文件是由AI生成的，还未经过测试")
    cmd = ["sudo", "smartctl", "-H", device]
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10
        )
        if result.returncode != 0:
            logging.error(f"[SSD ERROR] {result.stderr.decode(errors='ignore')}")
            return "error"
        output = result.stdout.decode(errors="ignore")
        logging.info(f"[SSD STATUS] {output}")
        if "PASSED" in output:
            return "health"
        elif "FAILED" in output or "WARNING" in output or "Pre-fail" in output:
            return "danger"
        else:
            return "danger"  # 未知状态也视为警告
    except Exception as e:
        logging.error(f"[SSD EXCEPTION] {e}")
        return "error"
