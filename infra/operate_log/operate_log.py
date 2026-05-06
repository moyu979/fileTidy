import json
import os
from datetime import datetime

_logger = None   # ⭐ 全局单例


class EventLogger:
    def __init__(self, config: dict):
        log_config = config.get("log", {})
        self.base_path = log_config.get("operate_log_path", "./logs")

        os.makedirs(self.base_path, exist_ok=True)

    def log(self, event):
        record = self._serialize(event)

        filepath = self._get_log_file_path()
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def load_all(self):
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
        now = datetime.utcnow()
        filename = f"events-{now.year}-{now.month:02d}.log"
        return os.path.join(self.base_path, filename)

    def _serialize(self, event):
        return {
            "type": event.__class__.__name__,
            "data": event.__dict__,
            "timestamp": datetime.utcnow().isoformat()
        }


# ---------- 对外 API ----------

def setup_event_logger(config: dict):
    global _logger
    _logger = EventLogger(config)


def log_event(event):
    if _logger is None:
        raise RuntimeError("EventLogger not initialized")
    _logger.log(event)


def load_events():
    if _logger is None:
        raise RuntimeError("EventLogger not initialized")
    return _logger.load_all()