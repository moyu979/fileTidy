# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
"""infra/persistence 内部工具：领域枚举归一化。

ORM 枚举列只接受枚举成员；外部调用方（API/脚本/仓储直连）可能传入字符串
（值形式 "healthy" 或名称形式 "HEALTHY"）。写入前统一转成枚举成员，避免
把非法字符串落库导致读回时抛 LookupError。
"""

from __future__ import annotations

from enum import Enum
from typing import TypeVar

E = TypeVar("E", bound=Enum)


def coerce_enum(enum_type: type[E], value: object) -> E | None:
    """把 ``value`` 归一为 ``enum_type`` 成员；None/已是枚举成员时原样返回。

    Args:
        enum_type: 目标枚举类（如 DeviceState）。
        value: 枚举成员、值字符串（"healthy"）或名称字符串（"HEALTHY"）。

    Returns:
        枚举成员或 None。

    Raises:
        ValueError: 字符串既不匹配枚举值也不匹配枚举名时抛出。
        TypeError: 传入非字符串/非枚举对象时抛出。
    """
    if value is None or isinstance(value, enum_type):
        return value
    if isinstance(value, str):
        try:
            return enum_type(value)      # 值形式，如 DeviceState("healthy")
        except ValueError:
            pass
        try:
            return enum_type[value]      # 名称形式，如 DeviceState["HEALTHY"]
        except KeyError:
            pass
        raise ValueError(
            f"{value!r} 不是 {enum_type.__name__} 的合法状态（枚举值或名称）"
        )
    raise TypeError(
        f"{enum_type.__name__} 需要枚举成员或字符串，收到 {type(value).__name__}"
    )
