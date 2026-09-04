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

from domain.storage.device.base import Device
from domain.storage.device.enum import DeviceState
from domain.storage.device.events import (
    DeviceFieldUpdated,
    DeviceInfoChanged,
    DeviceInfoSet,
    DeviceRegistered,
    DeviceRemoved,
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

    def list_devices(self) -> list[str]:
        """列出所有已注册设备的 JSON 字符串列表。

        Returns:
            设备 JSON 字符串列表。
        """
        return [device.to_json() for device in self.device_repository.list_devices()]

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
            dtype=data.get("type"),
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
            ValueError: 设备已存在。
        """
        if self.device_repository.is_exist(device.serial):
            raise ValueError(f"device {device.serial} already exists")
        self.device_repository.reg_device(device)
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
            raise ValueError(f"device {serial} not found")
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
            raise ValueError(f"device {serial} not found")
        old = device.dtype
        self.device_repository.update_device(serial, type=dtype)
        log_event(DeviceFieldUpdated(serial, "type", old, dtype))
        return (old, dtype)

    def set_state(self, serial: str, state: DeviceState) -> tuple[DeviceState, DeviceState]:
        """更新设备状态。

        Args:
            serial: 设备序列号。
            state: 新状态。

        Returns:
            tuple[DeviceState, DeviceState]: (旧值, 新值)。
        """
        device = self.device_repository.get_device(serial)
        if device is None:
            raise ValueError(f"device {serial} not found")
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
            raise ValueError(f"device {serial} not found")
        old = device.capacity
        self.device_repository.update_device(serial, capacity=capacity)
        log_event(DeviceFieldUpdated(serial, "capacity", old, capacity))
        return (old, capacity)

    # ── info 操作（JSON 文本） ────────────────────────────────────

    @staticmethod
    def _parse_info(info_str: str | None) -> dict:
        """解析 info JSON 文本为字典，空值返回空字典。"""
        if not info_str:
            return {}
        try:
            return json.loads(info_str)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_info(self, serial: str, info: dict) -> tuple[dict, dict]:
        """全量替换 info（JSON 文本）。返回 (旧info, 新info)。"""
        device = self.device_repository.get_device(serial)
        if device is None:
            raise ValueError(f"device {serial} not found")
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
            raise ValueError(f"device {serial} not found")
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
            raise ValueError(f"device {serial} not found")
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
            raise ValueError(f"device {old_serial} not found")
        self.device_repository.update_serial(old_serial, new_serial)
        log_event(DeviceSerialChanged(old_serial=old_serial, new_serial=new_serial))
        return (old_serial, new_serial)

    def remove_device(self, serial: str) -> None:
        """软删除设备（标记 REMOVED）。

        Args:
            serial: 设备序列号。

        Raises:
            ValueError: 设备不存在。
            DeviceInUseError: 设备仍被超级设备/卷引用（透传自仓储层）。
        """
        self.device_repository.remove_device(serial)
        log_event(DeviceRemoved(serial))
