# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 基础设施日志模块 - 日志记录器配置

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infra.config.app_config import AppConfig


LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class MonthlyFileHandler(logging.Handler):
    """按月滚动的文件日志处理器，每月生成一个独立的日志文件。"""

    def __init__(self, log_dir, level=logging.INFO):
        """
        初始化 MonthlyFileHandler。

        Args:
            log_dir: 日志文件存放目录
            level: 日志级别，默认为 INFO
        """
        super().__init__(level)
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.current_file = None
        self.current_path = None

    def emit(self, record):
        """
        输出日志记录到按月滚动的文件中。

        Args:
            record: 日志记录对象
        """
        try:
            now = datetime.now()
            filename = f"app-{now.year}-{now.month:02d}.log"
            filepath = os.path.join(self.log_dir, filename)

            if self.current_path != filepath:
                if self.current_file:
                    self.current_file.close()
                self.current_file = open(filepath, "a", encoding="utf-8")
                self.current_path = filepath

            msg = self.format(record)
            self.current_file.write(msg + "\n")
            self.current_file.flush()

        except Exception:
            self.handleError(record)

    def flush(self):
        """
        刷新当前日志文件的缓冲区。
        """
        if self.current_file:
            self.current_file.flush()

    def close(self):
        """
        关闭当前日志文件并释放句柄，同时执行父类清理。
        """
        try:
            if self.current_file:
                self.current_file.close()
                self.current_file = None
                self.current_path = None
        finally:
            super().close()


def setup_logging(config: "AppConfig"):
    """
    根据配置初始化全局日志系统。

    配置从 AppConfig 的 log section 读取，支持 cli_log_level、
    file_log_level 和 service_log_path 等参数。

    Args:
        config: AppConfig 配置容器实例
    """
    log_cfg = config["log"]

    cli_level = LOG_LEVEL_MAP.get(
        str(log_cfg.get("cli_log_level", "INFO")).upper(), logging.INFO
    )
    file_level = LOG_LEVEL_MAP.get(
        str(log_cfg.get("file_log_level", "INFO")).upper(), logging.INFO
    )

    log_path = log_cfg.get("service_log_path", "./logs")
    os.makedirs(log_path, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 总开关，细分靠 handler
    for handler in root_logger.handlers:  # 先关闭旧 handler，避免文件句柄泄漏
        handler.close()
    root_logger.handlers.clear()

    file_handler = MonthlyFileHandler(log_path, level=file_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(cli_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)