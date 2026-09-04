# CHECK: 待检查 - 基础设施操作日志模块 - 操作日志记录

from __future__ import annotations

import json
import os
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infra.config.app_config import AppConfig

_logger = None   # ⭐ 全局单例


def _json_default(obj):
    """
    JSON 序列化时的默认类型处理器。

    支持 Enum 和 datetime 类型的序列化，其他类型抛出 TypeError。

    Args:
        obj: 需要序列化的对象

    Returns:
        序列化后的值

    Raises:
        TypeError: 对象类型不支持 JSON 序列化
    """
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class EventLogger:
    """事件日志记录器，将事件序列化为 JSON 并按月份写入日志文件。"""

    def __init__(self, config: "AppConfig"):
        """
        初始化 EventLogger。

        Args:
            config: AppConfig 容器实例，从中读取 operation_log_path
        """
        log_config = config["log"]
        self.base_path = log_config.get("operation_log_path", "./logs")

        os.makedirs(self.base_path, exist_ok=True)

    def log(self, event):
        """
        记录一个事件到日志文件。

        Args:
            event: 事件对象，其 __dict__ 将被序列化为 JSON
        """
        record = self._serialize(event)

        filepath = self._get_log_file_path()
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(record, ensure_ascii=False, default=_json_default) + "\n"
            )

    def load_all(self):
        """
        加载所有已记录的事件日志。

        遍历日志目录中所有 .log 文件，按文件名排序后逐行解析 JSON。

        Returns:
            所有事件的字典列表
        """
        records = []

        for filename in sorted(os.listdir(self.base_path)):
            if not filename.endswith(".log"):
                continue

            filepath = os.path.join(self.base_path, filename)

            with open(filepath, encoding="utf-8") as f:
                for line in f:
                    records.append(json.loads(line))

        return records

    def _get_log_file_path(self):
        """
        根据当前 UTC 时间生成当月日志文件的路径。

        Returns:
            形如 {base_path}/events-YYYY-MM.log 的文件路径
        """
        now = datetime.utcnow()
        filename = f"events-{now.year}-{now.month:02d}.log"
        return os.path.join(self.base_path, filename)

    def _serialize(self, event):
        """
        将事件对象序列化为字典。

        Args:
            event: 事件对象

        Returns:
            包含 type、timestamp 和 data 的字典
        """
        return {
            "type": event.__class__.__name__,
            "timestamp": datetime.utcnow().isoformat(),
            "data": event.__dict__
        }


# ---------- 对外 API ----------

def setup_event_logger(config: "AppConfig"):
    """
    初始化全局事件日志器。

    Args:
        config: AppConfig 配置容器实例
    """
    global _logger
    _logger = EventLogger(config)


def log_event(event):
    """
    记录一个事件到全局事件日志器。

    Args:
        event: 事件对象

    Raises:
        RuntimeError: 全局事件日志器未初始化
    """
    if _logger is None:
        raise RuntimeError("EventLogger not initialized")
    _logger.log(event)


def load_events():
    """
    从全局事件日志器加载所有已记录的事件。

    Returns:
        所有事件的字典列表

    Raises:
        RuntimeError: 全局事件日志器未初始化
    """
    if _logger is None:
        raise RuntimeError("EventLogger not initialized")
    return _logger.load_all()