# CHECK: AI生成 - 配置内容管理纯接口（无数据、无锁、无实现）

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ConfigContentManager(ABC):
    """配置内容管理接口（纯接口，无状态无实现）。

    约束所有介入的配置类（SingleFileConfig / SystemConfig 及未来 conf）实现统一的
    取数/刷新契约，供配置容器（AppConfig）统一调度。
    热更新（on_change / stop_auto_reload / is_auto_reload_running）是 SingleFileConfig
    的扩展能力，不属于本接口。
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """宽松读取配置项。

        Args:
            key (str): 配置项键名。
            default (Any): 缺失时返回的默认值。

        Returns:
            Any: 配置项的值，或 default。
        """

    @abstractmethod
    def get_required(self, key: str) -> Any:
        """严格读取必填项。

        Args:
            key (str): 配置项键名。

        Returns:
            Any: 配置项的值。

        Raises:
            KeyError: key 缺失时。
        """

    @abstractmethod
    def __getitem__(self, key: str) -> Any:
        """按 key 读取（config[key]）。

        Args:
            key (str): 配置项键名。

        Returns:
            Any: 配置项的值。

        Raises:
            KeyError: key 缺失时。
        """

    @abstractmethod
    def __contains__(self, key: object) -> bool:
        """判断配置项是否存在。

        Args:
            key (object): 配置项键名。

        Returns:
            bool: 是否存在。
        """

    @property
    @abstractmethod
    def data(self) -> dict[str, Any]:
        """当前配置内容快照（拷贝）。

        Returns:
            dict[str, Any]: 全部配置项拷贝。
        """

    @abstractmethod
    def reload(self) -> bool:
        """刷新配置内容。

        Returns:
            bool: 是否有变化；无热更能力返回 False。
        """
