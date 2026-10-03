# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: ai生成，待检查
# CHECK: 待检查 - 应用层 Device 服务 - 设备业务用例编排

"""
设备服务 —— 去掉 DeviceSystemPort 依赖，直接调用系统函数。
保留类结构和 repository 注入，仓库保持原样。
"""

import json
import logging
import os
from datetime import datetime

from domain.common.json_utils import parse_json_object
from domain.storage.device.base import Device
from domain.storage.device.enum import DeviceState
from domain.storage.device.errors import (
    DeviceAlreadyRegisteredError,
    DeviceAlreadyRemovedError,
    DeviceNotFoundError,
)
from domain.storage.device.events import (
    DeviceFieldUpdated,
    DeviceInfoChanged,
    DeviceInfoSet,
    DeviceRegistered,
    DeviceRemoved,
    DeviceRevived,
    DeviceSerialChanged,
)
from infra.common.time_defaults import LAST_CHECK_TIME_ORIGIN
from infra.operation_log.operation_log import log_event
from infra.system.path_manager.is_path import is_path

logger = logging.getLogger(__name__)


class DeviceService:
    """设备服务类。

    提供设备的注册（通过路径或信息）、加载、查询、字段更新等业务逻辑。
    """
    def __init__(self, device_repository) -> None:
        """初始化设备服务。

        Args:
            device_repository: 设备仓储实例。
        """
        self.device_repository = device_repository
        logger.info("Device service initialized")


    def load_device(
        self,
        serial: str | None = None,
        device_path: str | None = None,
    ) -> str | None:
        """加载设备，支持通过序列号或路径查询。

        Args:
            serial: 设备序列号。
            device_path: 设备路径。

        Returns:
            设备 JSON 字符串，未找到时返回 None。
        """
        if serial is not None:
            device = self.device_repository.get_device(serial)
        elif device_path is not None:
            target = os.path.abspath(device_path)
            device = next(
                (
                    d
                    for d in self.device_repository.list_devices()
                    if d.device_path and os.path.abspath(d.device_path) == target
                ),
                None,
            )
        else:
            device = None
        return device.to_json() if device else None

    def load_device_by_target(self, target: str, field: str | None = None) -> str | None:
        """根据目标值加载设备。

        自动识别 target 是路径还是序列号。

        Args:
            target: 目标值（路径或序列号）。
            field: 指定匹配的字段名，None 表示自动识别。

        Returns:
            设备 JSON 字符串，未找到时返回 None。
        """
        if field is None:
            if is_path(target):
                return self.load_device(device_path=target, serial=None)
            return self.load_device(serial=target, device_path=None)
        # TODO: 按指定字段查询
        raise NotImplementedError(f"按字段 {field} 查询尚未实现")

    def list_devices(self, exclude_removed: bool = True) -> list[str]:
        """列出设备的 JSON 字符串列表。

        Args:
            exclude_removed: 为 True（默认）时排除已移除（REMOVED）的设备。

        Returns:
            设备 JSON 字符串列表。
        """
        return [
            device.to_json()
            for device in self.device_repository.list_devices(
                exclude_removed=exclude_removed
            )
        ]

    # ── 登记（增） ────────────────────────────────────────────────

    # TODO: 在线登记 reg_device_probed（待实现）
    #   - 探测编排：归一化 path → 调 infra/system 探测函数采集 serial/type/capacity/state
    #   - 冲突/对比：采集值 vs 传入值；冲突交互方案待定（原 domain/common/conflict.py 已删）
    #   - device_path 不落库（可能变化），在线探测到的路径按需使用即可
    #   - 复用下方 _commit 公共提交段；CLI do_reg 的 path 分支待接回
    def reg_device_manual(self, data: dict) -> str:
        """离线手动登记设备：无探测、无对比、无冲突。

        用户提供序列号及（可选的）其余字段，系统不探测、不自动采集，
        直接用传入值 + 默认值构造设备并落库。在线登记（自动采集 +
        冲突裁决）规划中，将实现为 reg_device_probed，与本方法共用
        _commit 公共提交段。

        TODO(磁带 serial)：目前 serial 必填（缺→ValueError）。磁带理论上也可
        「有输入就用、没输入自动生成」——对齐 reg_super_device_manual 的 serial
        语义；若支持则在 serial 缺失且 dtype 为磁带时自动生成（如 generate_id）。

        Args:
            data: 设备字段字典，至少包含 "serial"。可选键：name / type /
                add_time / last_check_time / capacity / info / state。
                默认值：name→serial[:8]，add_time→now，
                last_check_time→LAST_CHECK_TIME_ORIGIN，state→UNKNOWN。

        Returns:
            登记成功的设备序列号。

        Raises:
            ValueError: serial 缺失或设备已存在。
        """
        serial = data.get("serial")
        if not serial:
            raise ValueError("reg_device_manual: 'serial' is required")

        device = Device.create(
            serial=serial,
            name=data.get("name") or serial[:8],
            dtype=data.get("dtype"),
            add_time=data.get("add_time") or datetime.now(),
            last_check_time=data.get("last_check_time") or LAST_CHECK_TIME_ORIGIN,
            capacity=data.get("capacity"),
            info=data.get("info"),
            state=data.get("state") or DeviceState.UNKNOWN,
        )
        return self._commit(device)

    def _commit(self, device: Device) -> str:
        """登记公共提交段：存在性校验 + 落库 + 事件。

        在线（reg_device_probed，规划中）与离线（reg_device_manual）
        登记共用此段，保证两个入口落库行为一致。

        Args:
            device: 已构造好的 Device 实例（serial 已确定）。

        Returns:
            登记成功的设备序列号。

        Raises:
            ValueError: 设备已存在；或已存在但处于 REMOVED
                （需先调用 revive_device 复活，而不是重新登记）。
        """
        # 判定与分类都已下沉到仓储：撞 REMOVED 行抛 DeviceAlreadyRemovedError，
        # 撞活跃行抛 DeviceAlreadyRegisteredError。本层只负责把事实翻译成给用户的措辞
        # —— 提示里点名 revive_device 属应用层编排，不应由仓储说出口。
        try:
            self.device_repository.reg_device(device)
        except DeviceAlreadyRemovedError as e:
            raise ValueError(
                f"device {e.serial} 已被移除（REMOVED），"
                f"如要重新启用请先调用 revive_device"
            ) from None
        except DeviceAlreadyRegisteredError as e:
            raise ValueError(f"device {e.serial} already exists") from None
        log_event(DeviceRegistered(device))
        return device.serial

    # ── 字段更新（TODO） ──────────────────────────────────────────

    def set_name(self, serial: str, name: str) -> tuple[str, str]:
        """更新设备名称。

        Args:
            serial: 设备序列号。
            name: 新名称。

        Returns:
            tuple[str, str]: (旧值, 新值)。
        """
        device = self.device_repository.get_device(serial)
        if device is None:
            raise DeviceNotFoundError(serial)
        old = device.name
        self.device_repository.update_device(serial, name=name)
        log_event(DeviceFieldUpdated(serial, "name", old, name))
        return (old, name)

    def set_type(self, serial: str, dtype: str) -> tuple[str, str]:
        """更新设备类型。

        Args:
            serial: 设备序列号。
            dtype: 新类型。

        Returns:
            tuple[str, str]: (旧值, 新值)。
        """
        device = self.device_repository.get_device(serial)
        if device is None:
            raise DeviceNotFoundError(serial)
        old = device.dtype
        self.device_repository.update_device(serial, dtype=dtype)
        log_event(DeviceFieldUpdated(serial, "dtype", old, dtype))
        return (old, dtype)

    # TODO(P1): set_state 目前能直接把设备改成 REMOVED，**绕过 remove_device 的引用校验**
    #   （remove_device 要求：无 USING 的超级设备子项关联、无未移除的卷）。
    #   后果：一台正被超级设备使用的设备可以被静默标成 REMOVED，破坏引用不变式。
    #   收口方向（未定稿）：① set_state 拒绝 REMOVED，强制改走 remove_device；
    #   ② 或在 set_state 内部复用 remove_device 的那套校验。
    #   注意：仓储层已禁止 update_device 写入 REMOVED，因此 set_state(REMOVED)
    #   现在会直接报错（相当于先行收口了路径 ①）；软删除走 remove_device，
    #   复活走 revive_device。本方法自身的收口整理仍待办。
    def set_state(self, serial: str, state: DeviceState) -> tuple[DeviceState, DeviceState]:
        """更新设备状态。

        注意：本方法不校验设备是否被引用，因此**不应**用它把设备置为 REMOVED；
        软删除请走 `remove_device`（带着引用校验）。详见上方 TODO。

        Args:
            serial: 设备序列号。
            state: 新状态。

        Returns:
            tuple[DeviceState, DeviceState]: (旧值, 新值)。
        """
        device = self.device_repository.get_device(serial)
        if device is None:
            raise DeviceNotFoundError(serial)
        old = device.state
        self.device_repository.update_device(serial, state=state)
        log_event(DeviceFieldUpdated(serial, "state", old, state))
        return (old, state)

    def set_capacity(self, serial: str, capacity: int) -> tuple[int, int]:
        """更新设备容量。

        Args:
            serial: 设备序列号。
            capacity: 新容量（字节）。

        Returns:
            tuple[int, int]: (旧值, 新值)。
        """
        device = self.device_repository.get_device(serial)
        if device is None:
            raise DeviceNotFoundError(serial)
        old = device.capacity
        self.device_repository.update_device(serial, capacity=capacity)
        log_event(DeviceFieldUpdated(serial, "capacity", old, capacity))
        return (old, capacity)

    # ── info 操作（JSON 文本） ────────────────────────────────────

    @staticmethod
    def _parse_info(info_str: str | None) -> dict:
        """解析 info JSON 文本为字典（薄封装，逻辑见 parse_json_object）。"""
        return parse_json_object(info_str)

    def set_info(self, serial: str, info: dict) -> tuple[dict, dict]:
        """全量替换 info（JSON 文本）。返回 (旧info, 新info)。"""
        device = self.device_repository.get_device(serial)
        if device is None:
            raise DeviceNotFoundError(serial)
        old = self._parse_info(device.info)
        new_str = json.dumps(info, ensure_ascii=False)
        self.device_repository.update_device(serial, info=new_str)
        log_event(DeviceInfoSet(serial, old, info))
        return (old, info)

    def append_info(self, serial: str, data: dict) -> tuple[dict, dict]:
        """合并键值对到现有 info（JSON 文本）。返回 (旧info, 新info)。

        逐键记录 DeviceInfoChanged：旧有键 → replace；新增键 → add。
        """
        device = self.device_repository.get_device(serial)
        if device is None:
            raise DeviceNotFoundError(serial)
        old = self._parse_info(device.info)
        new_info = {**old, **data}
        new_str = json.dumps(new_info, ensure_ascii=False)
        self.device_repository.update_device(serial, info=new_str)
        for key, new_val in data.items():
            if key in old:
                log_event(DeviceInfoChanged(serial, "replace", key, old[key], new_val))
            else:
                log_event(DeviceInfoChanged(serial, "add", key, None, new_val))
        return (old, new_info)

    def delete_info(self, serial: str, key: str) -> tuple[dict, dict]:
        """从 info 中删除指定键（JSON 文本）。返回 (旧info, 新info)。"""
        device = self.device_repository.get_device(serial)
        if device is None:
            raise DeviceNotFoundError(serial)
        old = self._parse_info(device.info)
        new_info = dict(old)
        old_val = new_info.pop(key, None)
        new_str = json.dumps(new_info, ensure_ascii=False)
        self.device_repository.update_device(serial, info=new_str)
        if key in old:
            log_event(DeviceInfoChanged(serial, "remove", key, old_val, None))
        return (old, new_info)

    def set_serial(self, old_serial: str, new_serial: str) -> tuple[str, str]:
        """重置设备序列号，同步更新关联表。返回 (旧序列号, 新序列号)。"""
        if not self.device_repository.is_exist(old_serial):
            raise DeviceNotFoundError(old_serial)
        self.device_repository.update_serial(old_serial, new_serial)
        log_event(DeviceSerialChanged(old_serial=old_serial, new_serial=new_serial))
        return (old_serial, new_serial)

    def remove_device(self, serial: str) -> None:
        """软删除设备（标记 REMOVED）。

        事件携"删除前"快照，故先读一次原始实体（exclude_removed=False）再落库删除；
        不存在时由仓储的 remove_device 兜底报错。

        Args:
            serial: 设备序列号。

        Raises:
            DeviceNotFoundError: 设备不存在。
            DeviceAlreadyRemovedError: 设备已处于 REMOVED（不可重复移除，透传自仓储层）。
            DeviceInUseError: 设备仍被超级设备/卷引用（透传自仓储层）。
        """
        device = self.device_repository.get_device(serial, exclude_removed=False)
        if device is None:
            raise DeviceNotFoundError(serial)
        self.device_repository.remove_device(serial)
        log_event(DeviceRemoved(device))

    def revive_device(self, serial: str) -> None:
        """复活已移除（REMOVED）的设备（state 置回 UNKNOWN）。

        Args:
            serial: 设备序列号。

        Raises:
            DeviceNotFoundError: 设备不存在（透传自仓储层）。
            DeviceNotRemovedError: 设备未处于 REMOVED（无需复活，透传自仓储层）。
        """
        self.device_repository.revive_device(serial)
        log_event(DeviceRevived(serial))
