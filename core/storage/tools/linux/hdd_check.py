import subprocess
import logging


def run_command(cmd):
    """同步运行一个命令，并返回输出结果"""
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode, result.stdout.decode(), result.stderr.decode()


def hdd_check(device="/dev/sda"):
    """
    检查HDD健康状态，返回 'health'（健康）、'danger'（警告）、'error'（命令失败）
    """
    logging.warning("[AI WARNING] 这些文件是由AI生成的，还未经过测试")
    # 检查SMART
    cmd_smart = ["sudo", "smartctl", "-H", device]
    code, out, err = run_command(cmd_smart)
    if code != 0:
        logging.error(f"[HDD SMART ERROR] {err}")
        return "error"
    if "PASSED" not in out:
        logging.warning(f"[HDD SMART WARNING] {out}")
        return "danger"
    logging.info(f"[HDD SMART OK] {out}")
    # 检查坏道
    cmd_badblocks = ["sudo", "badblocks", "-sv", device]
    code, out, err = run_command(cmd_badblocks)
    if code != 0:
        logging.error(f"[HDD BADBLOCKS ERROR] {err}")
        return "error"
    if out.strip():
        logging.warning(f"[HDD BADBLOCKS WARNING] {out}")
        return "danger"
    logging.info(f"[HDD BADBLOCKS OK] {out}")
    return "health"
