import logging
import os
from pathlib import Path

from core.conf import get


def _resolve_log_level(level_value):
    """将字符串/数值映射为 logging 等级。"""
    if isinstance(level_value, int):
        return level_value
    if isinstance(level_value, str):
        level_name = level_value.upper()
        return getattr(logging, level_name, logging.INFO)
    return logging.INFO


def init_log(path=None):
    """根据配置初始化日志系统。

    优先顺序：
    - 参数 path 优先作为日志目录；若未提供则使用 conf.get("log_path")。
    - 文件名来自 conf.get("log_file")。
    - 等级来自 conf.get("log_level")。
    - 格式来自 conf.get("log_format")。
    - 若 conf.get("develop_mode") 为 True，则同时输出到控制台。
    """
    log_dir = path if path is not None else get("log_path")
    log_file = get("log_file")
    level = _resolve_log_level(get("log_level"))
    fmt = get("log_format") or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    develop_mode = bool(get("develop_mode"))

    if not log_dir:
        log_dir = "./log"
    if not log_file:
        log_file = "app.log"

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    formatter = logging.Formatter(fmt)
    file_handler.setFormatter(formatter)

    handlers = [file_handler]
    if develop_mode:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(formatter)
        handlers.append(stream_handler)

    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.handlers.clear()

    logging.basicConfig(level=level, handlers=handlers, format=fmt)

    # 附加一个简短的启动日志，便于确认路径与等级
    logging.getLogger(__name__).debug(
        "logging 初始化完成: path=%s level=%s develop_mode=%s", log_path, level, develop_mode
    )