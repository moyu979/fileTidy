# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 领域层 SingleSuperDevice 变体 - 单盘超级设备实现

import datetime
from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.enum import SuperDeviceState


class SingleSuperDevice(SuperDevice):
    """单设备超级设备类。

    继承自 SuperDevice 基类，代表仅包含单个物理设备的超级设备。
    构造时要求 devices 恰好 1 个元素；**例外**：处于 REMOVED（软删除）时允许 0 个
    —— 软删会释放子项关联（USING → SUPER_DEVICE_REMOVED），此时 0 子项是合法中间态。
    """
    _type_key = "single"

    # TODO(P3): 当前仅透传构造函数 + 断言，后续可添加单设备特有逻辑
    def __init__(self,
        serial: str,
        name: str,
        sdtype: str,
        need_all_devices_online: bool,
        add_time: datetime,
        last_check_time: datetime,
        state: SuperDeviceState,
        capacity: int,
        info: str,
        devices: list[str],
    ):
        """初始化单设备超级设备实例。

        Args:
            serial: 超级设备序列号。
            name: 超级设备名称。
            sdtype: 超级设备类型。
            need_all_devices_online: 是否需要设备在线。
            add_time: 添加时间。
            last_check_time: 最后一次检查时间。
            state: 超级设备状态。
            capacity: 总容量（字节）。
            info: 附加信息。
            devices: 子设备序列号列表（须恰好 1 个；state 为 REMOVED 时允许 0 个）。

        Raises:
            AssertionError: 非 REMOVED 状态下 devices 长度不为 1 时抛出。
        """
        super().__init__(serial, name, sdtype, need_all_devices_online,
                         add_time, last_check_time, state, capacity, info, devices)
        # 创建期不变式：single 必须恰好 1 个子项。
        # 例外：REMOVED（软删除）—— 软删会释放子项关联，故此时 0 子项合法。
        # 注：当前「摘子项」功能已停用，因此不存在「非 REMOVED 且 0 子项」的 single；
        #    若将来恢复摘子项，此处需重新评估（届时会出现非 REMOVED 的 0 子项）。
        assert self.is_removed() or len(devices) == 1, (
            f"SingleSuperDevice 需要恰好 1 个子设备（REMOVED 除外）："
            f"serial={serial}, state={state!r}, devices={devices!r}"
        )
        