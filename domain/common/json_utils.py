# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: ai生成，待检查 - 领域共享 JSON 解析工具

import json


def parse_json_object(text: str | None) -> dict:
    """解析 JSON 文本，且只接受「对象」（顶层为 dict）。

    本项目的 info 类字段一律存 JSON 对象文本，所以非对象 JSON
    （数组 / 数字 / 字符串）一律返回空字典，调用方不必再自己判类型。

    收敛自 device / super_device / volume / super_volume 实体基类的 `_parse_info`、
    四个 service 的静态 `_parse_info`、以及 super_device 仓储的 `_parse_structure_info`。

    Args:
        text: JSON 文本，允许 None / 空串。

    Returns:
        解析后的 dict；输入为空、非法 JSON 或顶层不是对象时返回 {}。
    """
    if not text:
        return {}
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}
