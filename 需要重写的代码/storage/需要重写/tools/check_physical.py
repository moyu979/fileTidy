import asyncio
import logging
from storage.storage import Storage
import core.conf.conf as conf


async def run_command(cmd):
    """异步运行一个命令，并返回输出结果"""
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return process.returncode, stdout.decode(), stderr.decode()


async def check_smart_health(device="/dev/sda"):
    cmd = ["sudo", "smartctl", "-H", device]
    code, out, err = await run_command(cmd)
    if code != 0:
        print(f"[SMART ERROR] {err}")
    else:
        print(f"[SMART OK] {device}\n{out}")


async def check_badblocks(device="/dev/sda"):
    cmd = ["sudo", "badblocks", "-sv", device]
    print(f"[{device}] Running badblocks scan...")
    code, out, err = await run_command(cmd)
    if code != 0:
        print(f"[BADBLOCKS ERROR] {err}")
    else:
        print(f"[BADBLOCKS OK] {device}\n{out}")


async def main():
    # 可并发检查多个磁盘
    await asyncio.gather(check_smart_health("/dev/sdb"), check_badblocks("/dev/sdc"))


# 运行
asyncio.run(main())


def check_physical(physical: Storage, option="smartctl"):
    if physical.get("kind") in conf.get("HDD"):
        check_hdd(physical)
    elif physical.get("kind") in conf.get("ssd"):
        check_ssd(physical)
    elif physical.get("kind") in conf.get("tape"):
        check_tape(physical)


def check_hdd(physical: Storage):
    logging.info(f"检查机械硬盘{physical.get("id")}")
    pass


def check_ssd(physical: Storage):

    pass


def check_tape(physical: Storage):
    pass
