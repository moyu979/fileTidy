# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""单测：infra/log/logger —— 日志系统。

目的：验证 MonthlyFileHandler 按月写文件、setup_logging 装配根 logger。

输入：临时日志目录与假 AppConfig。
期望输出：日志文件生成且包含记录；handler 从根 logger 可移除。
"""

from __future__ import annotations

import logging
from datetime import datetime

from infra.log.logger import MonthlyFileHandler, setup_logging


class _FakeLogConfig:
    def __getitem__(self, key):
        assert key == "log"
        return {
            "cli_log_level": "DEBUG",
            "file_log_level": "INFO",
            "service_log_path": str(self.path),
        }

    def __init__(self, path):
        self.path = path


def _clear_root_handlers(handlers):
    root = logging.getLogger()
    for h in handlers:
        root.removeHandler(h)
        h.close()


def test_monthly_handler_writes_current_month_file(tmp_path):
    """emit 一条日志 → 当月 app-YYYY-MM.log 出现并包含消息。"""
    handler = MonthlyFileHandler(str(tmp_path), level=logging.INFO)
    handler.setFormatter(logging.Formatter("%(message)s"))
    try:
        handler.emit(logging.LogRecord(
            name="t", level=logging.INFO, pathname=__file__,
            lineno=1, msg="hello monthly log", args=(), exc_info=None,
        ))
        now = datetime.now()
        logfile = tmp_path / f"app-{now.year}-{now.month:02d}.log"
        assert logfile.is_file()
        assert "hello monthly log" in logfile.read_text(encoding="utf-8")
    finally:
        handler.close()


def test_setup_logging_installs_handlers(tmp_path):
    """setup_logging → 根 logger 安装 file+console 两个 handler 并写文件。"""
    root = logging.getLogger()
    original = list(root.handlers)
    try:
        setup_logging(_FakeLogConfig(tmp_path))
        assert len(root.handlers) >= 2
        logging.getLogger("some.module").info("a log line for setup test")
        files = list(tmp_path.glob("app-*.log"))
        assert len(files) == 1
        assert "a log line for setup test" in files[0].read_text(encoding="utf-8")
    finally:
        added = [h for h in root.handlers if h not in original]
        _clear_root_handlers(added)
