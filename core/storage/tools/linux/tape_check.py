import subprocess
import logging

# 警告：这些文件是由AI生成的，还未经过测试


def tape_check(device="/dev/nst0"):
    """
    检查磁带健康状态，返回 'health'（健康）、'danger'（警告）、'error'（命令失败）
    """
    logging.warning("[AI WARNING] 这些文件是由AI生成的，还未经过测试")
    cmd_status = ["mt", "-f", device, "status"]
    try:
        result = subprocess.run(
            cmd_status, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10
        )
        if result.returncode != 0:
            logging.error(f"[TAPE ERROR] {result.stderr.decode(errors='ignore')}")
            return "error"
        output = result.stdout.decode(errors="ignore")
        logging.info(f"[TAPE STATUS] {output}")
        # 简单判断：如果包含 BOT（磁带头）或 ONLINE 等字样，认为健康
        if any(x in output for x in ["ONLINE", "BOT", "READY", "OK"]):
            return "health"
        # 如果包含 EOT（磁带尾）、FAULT、ERROR 等字样，认为危险
        if any(x in output for x in ["EOT", "FAULT", "ERROR", "OFFLINE"]):
            return "danger"
        # 其它未知状态也视为警告
        return "danger"
    except Exception as e:
        logging.error(f"[TAPE EXCEPTION] {e}")
        return "error"
