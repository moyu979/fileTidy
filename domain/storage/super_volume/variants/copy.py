# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 领域层 Copy 变体 - 复制超级卷实现

from __future__ import annotations

import datetime

from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.enum import SuperVolumeState


class CopySuperVolume(SuperVolume):
    """复制超级卷类。

    继承自 SuperVolume 基类，代表通过复制方式使多个卷内容保持一致的超级卷。
    """
    _type_key = "copy"

    # TODO(P3): 当前仅透传构造函数，无任何子类特有行为，后续可添加复制一致性校验等逻辑
    def __init__(
        self,
        serial: str,
        name: str,
        svtype: str,
        method: str,
        add_time: datetime.datetime,
        last_check_time: datetime.datetime,
        state: SuperVolumeState,
        info: str,
        volumes: list[str],
    ) -> None:
        """初始化复制超级卷实例。

        Args:
            serial: 超级卷序列号。
            name: 超级卷名称。
            svtype: 超级卷类型。
            method: 组合方法。
            add_time: 添加时间。
            last_check_time: 最后一次检查时间。
            state: 超级卷状态。
            info: 附加信息。
            volumes: 子卷序列号列表。
        """
        super().__init__(
            serial, name, svtype, method,
            add_time, last_check_time, state, info, volumes,
        )
