# 本文件未经测试
"""
配置模块对外接口。

用法示例：

    from core.conf import init_conf, get, set, map_kind_to_type

    init_conf()  # 或者在首次调用 get/set 时由内部 ensure_initialized() 惰性初始化
    system = get("system")
    ok = set("system", "Linux")
    disk_type = map_kind_to_type("LTO7")

注意：导入本包不会进行任何 IO 或初始化，保持零副作用。
"""

from .conf import (
    init_conf,
    load_json,
    dump_json,
    get,
    set,
    map_kind_to_type,
)

__all__ = [
    "init_conf",
    "load_json",
    "dump_json",
    "get",
    "set",
    "map_kind_to_type",
]
