"""简单的配置管理器，目前仅负责数据库路径。"""

from __future__ import annotations

import os
import platform
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


_DEFAULT_VALUES = {
    "path": "./data/datas.db",
    "hash_check_memery":512,
    "machine_id": "0",  # 机器ID，范围0-9999，用于多机器环境区分
}

_ENV_KEYS: Dict[str, str] = {
    "path": "FILETIDY_DB_PATH",
}

@dataclass
class _ConfState:
    values: Dict[str, str]
    
    def keys(self):
        return list(self.values.keys())

class ConfManager:
    """集中管理配置，目前仅维护数据库路径，使用简单的字典验证。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()

        state_values = _DEFAULT_VALUES.copy()
        self._state = _ConfState(values=state_values)

        # 初始化时尝试从环境变量覆盖配置
        self.load_from_env()

        self.set("system", self.get_system())


    # 读取 -----------------------------------------------------------------
    def get(self, key: str) -> str:
        """获取配置值，目前支持 key='path'。"""
        if key not in self._state.keys():
            raise KeyError(f"未知配置项: {key}")
        with self._lock:
            print(111)
            return str(self._state.values[key])

    # 写入 -----------------------------------------------------------------
    def set(self, key: str, value: str | os.PathLike[str]) -> None:
        """设置配置值，目前支持 key='path'。"""
        with self._lock:
            self._state.values[key] = value

    def load_from_env(self) -> bool:
        """遍历所有支持的环境变量进行覆盖，成功至少一项返回 True。"""
        updated = False
        for key, env_key in _ENV_KEYS.items():
            if key not in _DEFAULT_VALUES:
                continue
            value = os.getenv(env_key)
            if not value:
                continue
            self.set(key, value)
            updated = True
        return updated
    
    def get_system(self) -> str:
        #完成一个功能，获取系统的名称，如果系统是windows，则返回windows，如果系统是linux，则返回linux，如果系统是macos，则返回macos，如果系统是其他，则返回其他
        system = platform.system()
        if system == "Windows":
            return "windows"
        elif system == "Linux":
            return "linux"
        elif system == "Darwin":
            return "macos"
        else:
            return "other"


conf_manager: Optional[ConfManager] = None


def init_conf_manager() -> ConfManager:
    """初始化配置管理器（幂等）。"""
    global conf_manager
    if conf_manager is None:
        conf_manager = ConfManager()
    return conf_manager


def get_conf_manager() -> ConfManager:
    if conf_manager is None:
        init_conf_manager()
    return conf_manager


__all__ = ["ConfManager", "conf_manager", "init_conf_manager", "get_conf_manager"]


