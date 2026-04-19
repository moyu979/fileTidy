from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, ItemsView, KeysView, ValuesView

import yaml

SectionDict = dict[str, Any]


class Config:
    """从 ``data_dir/settings`` 下的 YAML 加载配置。"""

    def __init__(self, args: argparse.Namespace) -> None:
        self._args = args
        self.data_dir = Path(args.data_dir).expanduser().resolve()
        self.settings_dir = self.data_dir / "settings"
        self._sections: dict[str, SectionDict] = {}
        self.load()

    @property
    def args(self) -> argparse.Namespace:
        return self._args

    def __getitem__(self, key: str) -> SectionDict:
        return self._sections[key]

    def get(self, key: str, default: SectionDict | None = None) -> SectionDict | None:
        return self._sections.get(key, default)

    def __contains__(self, key: object) -> bool:
        return key in self._sections

    def keys(self) -> KeysView[str]:
        return self._sections.keys()

    def items(self) -> ItemsView[str, SectionDict]:
        return self._sections.items()

    def values(self) -> ValuesView[SectionDict]:
        return self._sections.values()

    def load(self) -> dict[str, SectionDict]:
        if not self.settings_dir.is_dir():
            raise FileNotFoundError(f"settings 目录不存在: {self.settings_dir}")

        self._sections = {}
        paths: list[Path] = []
        seen: set[Path] = set()
        for pattern in ("*.yaml", "*.yml"):
            for p in sorted(self.settings_dir.glob(pattern)):
                key = p.resolve()
                if key in seen:
                    continue
                seen.add(key)
                paths.append(p)

        for path in paths:
            stem = path.stem
            if stem in self._sections:
                raise ValueError(
                    f"settings 中存在重复的键 {stem!r}（请避免同名 .yaml/.yml）"
                )
            text = path.read_text(encoding="utf-8")
            raw = yaml.safe_load(text) if text.strip() else {}
            if raw is None:
                raw = {}
            if not isinstance(raw, dict):
                raise ValueError(
                    f"{path} 根节点必须是映射（dict），实际为 {type(raw).__name__}"
                )
            self._sections[stem] = raw  # type: ignore[assignment]

        self._sections = self._replace_workspace_path(self._sections)
        self._sections["base"]["workspace_path"] = str(self.data_dir)
        return dict(self._sections)

    def _replace_workspace_path(self, obj: Any) -> Any:
        token = "${workspace_path}"
        replacement = str(self.data_dir)

        if isinstance(obj, str):
            return obj.replace(token, replacement)
        if isinstance(obj, dict):
            return {k: self._replace_workspace_path(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._replace_workspace_path(v) for v in obj]
        if isinstance(obj, tuple):
            return tuple(self._replace_workspace_path(v) for v in obj)

        return obj

    def __str__(self, *, indent: int | None = 2, ensure_ascii: bool = False) -> str:
        """将当前已加载的配置（各 yaml 合并后的 dict）序列化为 JSON 字符串。"""
        return json.dumps(
            self._sections,
            ensure_ascii=ensure_ascii,
            indent=indent,
            default=str,
        )

    @property
    def sections(self) -> dict[str, SectionDict]:
        return dict(self._sections)
