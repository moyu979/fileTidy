"""配置包的对外接口。"""

from .manager import (
    ConfManager,
    conf_manager,
    get_conf_manager,
    init_conf_manager,
)

__all__ = [
    "ConfManager",
    "conf_manager",
    "init_conf_manager",
    "get_conf_manager",
]


