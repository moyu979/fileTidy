# CHECK: AI生成 - 应用配置容器（共享 ConfigWatcher + SingleFileConfig 字典 + SystemConfig section）

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, ItemsView, KeysView, ValuesView

from infra.config.interface import ConfigContentManager
from infra.config.single_file_config import SingleFileConfig
from infra.config.system_config import SystemConfig
from infra.config.watcher import ConfigWatcher

logger = logging.getLogger(__name__)


class AppConfig:
    """settings 目录下多个 YAML 配置的容器，并内置 ``system`` section。

    传入 settings 根目录与可选 ``workspace_path``（``${workspace_path}`` 占位符根目录），
    内部据此构造替换表、创建共享 ConfigWatcher；对每个 .yaml/.yml 建 SingleFileConfig，
    以 stem 为 key 存入字典并透传替换表。查询与 SingleFileConfig 一致，仅参数后移
    一位、首参为 section 名::

        conf["restapi"]["port"]        # 两层索引
        conf.get("restapi", "port")    # get(section, key, default=None)
        conf.get_required("log", "cli_log_level")
        conf["system"]["cpu_count"]    # 系统配置 section
        conf.data                      # {section: 配置数据}
    """

    SYSTEM_SECTION = "system"   # SystemConfig 的内置 section 名

    def __init__(
        self,
        settings_dir: str | Path,
        workspace_path: str | Path | None = None,
    ) -> None:
        """扫描 YAML 建子配置，并内置 SystemConfig section。

        Args:
            settings_dir (str | Path): settings 根目录。
            workspace_path (str | Path | None): 可选，``${workspace_path}`` 占位符根目录；内部据此构造替换表透传给各 YAML 子配置。

        Raises:
            FileNotFoundError: 任一 YAML 缺失（由 SingleFileConfig 构造抛出）。
            yaml.YAMLError: YAML 解析失败（由 SingleFileConfig 构造抛出）。
            ValueError: YAML 根节点不是映射（由 SingleFileConfig 构造抛出）。
        """
        self.settings_dir = Path(settings_dir).expanduser().resolve()
        self.watcher = ConfigWatcher(self.settings_dir)
        replacements = (
            {"workspace_path": str(Path(workspace_path).expanduser().resolve())}
            if workspace_path
            else None
        )
        self._sections: dict[str, ConfigContentManager] = {}
        for yaml_path in self._collect_yaml_paths():
            self._sections[yaml_path.stem] = SingleFileConfig(
                yaml_path, self.watcher, replacements=replacements
            )
        self._sections[self.SYSTEM_SECTION] = SystemConfig()
        logger.info(
            "AppConfig constructed: settings=%s, sections=%s",
            self.settings_dir,
            sorted(self._sections),
        )

    def _collect_yaml_paths(self) -> list[Path]:
        """收集 settings 目录下所有 .yaml/.yml 文件，按文件名排序。

        Returns:
            list[Path]: 文件路径列表。
        """
        paths: list[Path] = []
        seen: set[Path] = set()
        for pattern in ("*.yaml", "*.yml"):
            for p in sorted(self.settings_dir.glob(pattern)):
                key = p.resolve()
                if key in seen:
                    continue
                seen.add(key)
                paths.append(p)
        return paths

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """section 内宽松读取，仅用于可选项。

        Args:
            section (str): section 名（yaml 文件名或 system）。
            key (str): 配置项键名。
            default (Any): 缺失时返回的默认值。

        Returns:
            Any: 配置项的值，或 default。
        """
        return self._sections[section].get(key, default)

    def get_required(self, section: str, key: str) -> Any:
        """section 内严格读取必填项。

        Args:
            section (str): section 名（yaml 文件名或 system）。
            key (str): 配置项键名。

        Returns:
            Any: 配置项的值。

        Raises:
            KeyError: section 不存在，或 section 内 key 缺失。
        """
        return self._sections[section].get_required(key)

    def __getitem__(self, section: str) -> ConfigContentManager:
        """按 section 名取子配置，可继续链式查询。

        Args:
            section (str): section 名。

        Returns:
            ConfigContentManager: 子配置实例。

        Raises:
            KeyError: section 不存在。
        """
        return self._sections[section]

    def __contains__(self, section: object) -> bool:
        """判断 section 是否存在。

        Args:
            section (object): section 名。

        Returns:
            bool: 是否存在。
        """
        return section in self._sections

    def keys(self) -> KeysView[str]:
        """返回所有 section 名视图。

        Returns:
            KeysView[str]: section 名视图。
        """
        return self._sections.keys()

    def items(self) -> ItemsView[str, ConfigContentManager]:
        """返回 (section, 子配置) 视图。

        Returns:
            ItemsView[str, ConfigContentManager]: 视图。
        """
        return self._sections.items()

    def values(self) -> ValuesView[ConfigContentManager]:
        """返回所有子配置视图。

        Returns:
            ValuesView[ConfigContentManager]: 视图。
        """
        return self._sections.values()

    @property
    def data(self) -> dict[str, dict[str, Any]]:
        """所有 section 配置数据的快照。

        Returns:
            dict[str, dict[str, Any]]: {section: 数据}。
        """
        return {name: cfg.data for name, cfg in self._sections.items()}

    def reload(self, section: str | None = None) -> list[bool] | bool:
        """热重载指定 section；不指定则重载全部。

        Args:
            section (str | None): section 名；None 表示全部。

        Returns:
            list[bool] | bool: 是否有变化；重载全部时返回列表（system 恒为 False）。
        """
        if section is None:
            return [cfg.reload() for cfg in self._sections.values()]
        return self._sections[section].reload()

    def on_change(self, section: str, callback: Callable[[list[str]], None]) -> None:
        """注册指定 section 的变更回调。

        Args:
            section (str): section 名。
            callback (Callable[[list[str]], None]): 收到变化的键名列表。

        Raises:
            TypeError: 该 section 无热更能力（如 system）。
        """
        cfg = self._sections[section]
        if not hasattr(cfg, "on_change"):
            raise TypeError(f"section {section!r} 无热更能力（{type(cfg).__name__}）")
        cfg.on_change(callback)

    def stop_auto_reload(self, section: str | None = None) -> None:
        """注销指定或全部 section 的文件监听（无热更能力的 section 自动跳过）。

        Args:
            section (str | None): section 名；None 表示全部。
        """
        if section is None:
            for cfg in self._sections.values():
                if hasattr(cfg, "stop_auto_reload"):
                    cfg.stop_auto_reload()
        else:
            cfg = self._sections[section]
            if hasattr(cfg, "stop_auto_reload"):
                cfg.stop_auto_reload()

    @property
    def is_auto_reload_running(self) -> bool:
        """共享 watcher 是否正在运行。

        Returns:
            bool: 是否运行。
        """
        return self.watcher.is_running
