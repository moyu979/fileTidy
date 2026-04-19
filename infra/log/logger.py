# infrastructure/logging_config.py

import logging
import os
from logging.handlers import TimedRotatingFileHandler


LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

import logging
import os
from datetime import datetime


class MonthlyFileHandler(logging.Handler):
    def __init__(self, log_dir, level=logging.INFO):
        super().__init__(level)
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.current_file = None
        self.current_path = None

    def emit(self, record):
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


def setup_logging(config: dict):
    log_cfg = config.get("log", {})

    cli_level = LOG_LEVEL_MAP.get(log_cfg.get("cli_log_level", "INFO"), logging.INFO)
    file_level = LOG_LEVEL_MAP.get(log_cfg.get("service_log_level", "INFO"), logging.INFO)

    log_path = log_cfg.get("service_log_path", "./logs")
    os.makedirs(log_path, exist_ok=True)

    log_file = os.path.join(log_path, "app.log")

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 总开关，细分靠 handler
    root_logger.handlers.clear()

    # ✅ 文件日志（按月滚动）
    # file_handler = TimedRotatingFileHandler(
    #     log_file,
    #     when="midnight",   # 每天检查
    #     interval=1,
    #     backupCount=12,    # 保留12个月
    #     encoding="utf-8",
    # )
    file_handler = MonthlyFileHandler(log_path, level=file_level)
    file_handler.setFormatter(formatter)
    # file_handler.setLevel(file_level)
    # file_handler.setFormatter(formatter)
    # # 👇 关键：控制文件名为 年_月
    # file_handler.suffix = "%Y_%m.log"
    root_logger.addHandler(file_handler)

    # ✅ 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setLevel(cli_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)