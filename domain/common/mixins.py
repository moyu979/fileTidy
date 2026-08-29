# CHECK: ai生成，待检查 - 领域共享 JSON 序列化 Mixin

import json
from enum import Enum


class JsonSerializableMixin:
    """JSON 序列化 Mixin：提供 to_json / __str__ / _json_default / _ts。

    依赖子类实现 to_snapshot()（各实体字段不同，留在子类定义）。
    原分布在 device / super_device / volume / super_volume / file 五个实体
    基类中的重复序列化方法，统一收敛到这里（REFACTOR P0）。
    """
    def to_json(self) -> str:
        """将实体序列化为 JSON 字符串。

        Returns:
            JSON 格式的实体信息字符串。
        """
        return json.dumps(
            self.to_snapshot(),
            ensure_ascii=False,
            default=self._json_default,
        )

    def __str__(self) -> str:
        """返回实体的 JSON 字符串表示。

        Returns:
            JSON 格式的实体信息字符串。
        """
        return self.to_json()

    def _json_default(self, o: object) -> object:
        """JSON 序列化时的默认类型转换函数。

        处理 Enum 类型的序列化，将枚举值转换为其 value。

        Args:
            o: 需要序列化的对象。

        Returns:
            序列化后的值。

        Raises:
            TypeError: 对象类型不支持 JSON 序列化时抛出。
        """
        if isinstance(o, Enum):
            return o.value
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    def _ts(self, t):
        """将时间值格式化为 ISO 格式字符串。

        Args:
            t: 时间值，可为 datetime 对象或 None。

        Returns:
            ISO 格式的时间字符串，如果 t 为 None 则返回 None。
        """
        if t is None:
            return None
        if hasattr(t, "isoformat"):
            return t.isoformat()
        return t
