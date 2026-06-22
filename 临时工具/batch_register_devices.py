#!/usr/bin/env python3
"""
批量注册 24 个 LTO5 磁带设备（临时脚本）

用法:
    python 临时工具/batch_register_devices.py

说明:
    - 直接从 bootstrap 拉起应用，绕过交互式 CLI（即"劫持" cmdcli 调用链）
    - 注册 24 个 serial 从 20260220165613001 ∼ 20260220165613024 的设备
    - 类型均为 lto5，add_time=20260220165613，容量 1500 GiB
    - 操作日志会经由 infra/operate_log 正常写入
"""

import logging
import sys
import os
import time
from datetime import datetime

# ── 将项目根目录加入 sys.path ──────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from bootstrap import bootstrap
from setup import setup
from infra.config.config import Config
from shared.time_defaults import LAST_CHECK_TIME_ORIGIN
from domain.storage.device.enum import DeviceState

logger = logging.getLogger("batch_register_devices")


def _parse_addtime(text: str) -> datetime:
    """将 14 位时间字符串 '20260220165613' 解析为 datetime"""
    return datetime.strptime(text, "%Y%m%d%H%M%S")


def main():
    # ── 1. 接管 main.py 的启动逻辑 ──────────────────────────────────────────
    #     构建与 main.py 一致的参数，默认走 cli 模式
    from main import build_parser, parse_args
    args = parse_args(["--mode", "cli"])

    print("=" * 60)
    print("  批量注册 LTO5 设备脚本")
    print(f"  数据目录: {args.data_dir}")
    print("=" * 60)

    setup(args)
    app, config = bootstrap(args)

    device_service = app.device_service
    if device_service is None:
        logger.error("设备服务不可用，退出")
        sys.exit(1)

    # ── 2. 准备参数 ──────────────────────────────────────────────────────────
    SERIAL_PREFIX = "20260220165613"
    ADD_TIME = _parse_addtime("20260220165613")
    LAST_CHECK_TIME = LAST_CHECK_TIME_ORIGIN  # 使用跨层约定的未巡检占位时间
    CAPACITY = 1500 * 1000 * 1000 * 1000  # 1.5 TB (1000进制)
    DEVICE_TYPE = "lto5"
    DEVICE_NAME_PREFIX = "LTO5-Tape"
    INFO = "{}"
    STATE = DeviceState.UNKNOWN

    total = 24
    success = 0
    failed = 0

    print(f"\n开始批量注册 {total} 个 LTO5 设备 ...\n")
    print(f"{'序号':>4}  {'序列号':<22}  {'结果':<10}")
    print("-" * 42)

    start_time = time.time()

    for i in range(1, total + 1):
        serial = f"{SERIAL_PREFIX}{i:03d}"
        name = f"{DEVICE_NAME_PREFIX}-{i:03d}"

        try:
            result_json = device_service.reg_device_by_info(
                serial=serial,
                name=name,
                type=DEVICE_TYPE,
                add_time=ADD_TIME,
                last_check_time=LAST_CHECK_TIME,
                capacity=CAPACITY,
                info=INFO,
                state=STATE,
                device_path=None,
            )
            print(f"{i:>4}  {serial:<22}  ✅ 成功")
            success += 1
        except ValueError as e:
            # 已存在等业务异常
            print(f"{i:>4}  {serial:<22}  ❌ 失败: {e}")
            failed += 1
        except Exception as e:
            print(f"{i:>4}  {serial:<22}  ❌ 异常: {e}")
            failed += 1

        # ── 进度条（含已用时间和预估剩余时间） ──
        elapsed = time.time() - start_time
        avg_per_item = elapsed / i
        eta = avg_per_item * (total - i)

        # 格式化时间 mm:ss
        def _fmt(secs: float) -> str:
            m, s = divmod(int(round(secs)), 60)
            return f"{m:02d}:{s:02d}"

        bar_len = 30
        filled = int(bar_len * i / total)
        bar = "█" * filled + "░" * (bar_len - filled)
        print(
            f"  [{bar}] {i}/{total}  ┃ 已用 {_fmt(elapsed)}  ┃ 预估剩余 {_fmt(eta)}",
            end="\r",
            flush=True,
        )

    print()  # 换行，结束进度条行

    # ── 3. 汇总 ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  批量注册完成: 成功 {success} / 总数 {total}")
    if failed:
        print(f"  失败: {failed}")
    print("=" * 60)

    logger.info(
        "批量注册完成: 成功 %s / 总数 %s, 失败 %s",
        success, total, failed,
    )


if __name__ == "__main__":
    main()
