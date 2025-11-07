import subprocess


def run_command(cmd):
    """同步运行一个命令，并返回输出结果"""
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    return result.returncode, result.stdout.decode(errors='ignore'), result.stderr.decode(errors='ignore')
