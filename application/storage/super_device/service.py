# CHECK: 待检查 - 应用层 SuperDevice 服务 - 超级设备业务用例编排

from datetime import datetime
import json
import logging

from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.events import (
    SuperDeviceDeviceChanged,
    SuperDeviceFieldUpdated,
    SuperDeviceInfoChanged,
    SuperDeviceInfoSet,
    SuperDeviceRegistered,
    SuperDeviceRemoved,
    SuperDeviceSerialChanged,
)
from infra.operation_log.operation_log import log_event
from domain.storage.super_device.enum import SuperDeviceState
from infra.persistence.storage.super_device_repository import SuperDeviceRepository
from infra.system.path_manager.is_path import is_path
from infra.system.storage.device.get_serial import get_serial
from infra.common.id_generator import generate_id
from infra.common.time_defaults import LAST_CHECK_TIME_ORIGIN

logger = logging.getLogger(__name__)

class SuperDeviceService:
    """超级设备服务类。

    提供超级设备的注册、查询、字段更新和子设备管理等业务逻辑。
    """
    def __init__(self, super_device_repository, device_repository=None) -> None:
        """初始化超级设备服务。

        Args:
            super_device_repository: 超级设备仓储实例。
            device_repository: 设备仓储实例（可选）。
        """
        self.super_device_repository = super_device_repository
        self.device_repository = device_repository
        logger.info("SuperDeviceService initialized")

    def reg_super_device_manual(self, data: dict) -> str:
        """离线手动登记超级设备：serial 可选（有输入则用，无输入则自动生成）。

        用户提供 sdtype 及（可选的）其余字段；serial 未提供时由系统自动生成。
        不探测、不自动采集，直接按传入值 + 默认值构造并落库（公共提交段 _commit）。

        Args:
            data: 超级设备字段字典。可选键：serial / name / sdtype /
                need_all_devices_online / add_time / last_check_time / state /
                capacity / info / devices。默认值：serial→自动生成，name→serial[:8]，
                need_all_devices_online→True，add_time→now，
                last_check_time→LAST_CHECK_TIME_ORIGIN，state→HEALTHY，
                capacity→-1，info→""，devices→[]。

        Returns:
            登记成功的超级设备序列号。

        Raises:
            ValueError: sdtype 缺失。
        """
        serial = data.get("serial") or generate_id("")
        name = data.get("name") or serial[:8]
        sdtype = data.get("sdtype")
        if sdtype is None:
            raise ValueError("reg_super_device_manual: 'sdtype' is required")
        need_all_devices_online = data.get("need_all_devices_online")
        if need_all_devices_online is None:
            need_all_devices_online = True
        add_time = data.get("add_time") or datetime.now()
        last_check_time = data.get("last_check_time") or LAST_CHECK_TIME_ORIGIN
        state = data.get("state") or SuperDeviceState.HEALTHY
        capacity = data.get("capacity")
        if capacity is None:
            capacity = -1
        info = data.get("info") or ""
        sericals = []
        for device in data.get("devices", []):
            if is_path(device):
                sericals.append(get_serial(device))
            else:
                sericals.append(device)

        super_device = SuperDevice.create(
            serial=serial,
            name=name,
            sdtype=sdtype,
            need_all_devices_online=need_all_devices_online,
            add_time=add_time,
            last_check_time=last_check_time,
            state=state,
            capacity=capacity,
            info=info,
            devices=sericals,
        )
        return self._commit(super_device)

    def _commit(self, super_device: SuperDevice) -> str:
        """登记公共提交段：存在性校验 + 落库 + 事件。

        Args:
            super_device: 已构造好的 SuperDevice 实例（serial 已确定）。

        Returns:
            登记成功的超级设备序列号。

        Raises:
            ValueError: 超级设备已存在。
        """
        if self.super_device_repository.is_exist(super_device.serial):
            raise ValueError(f"super_device {super_device.serial} already exists")
        self.super_device_repository.reg_super_device(super_device)
        log_event(SuperDeviceRegistered(super_device))
        return super_device.serial

    def load_super_device(
        self,
        serial: str | None = None,
        super_device_path: str | None = None,
    ) -> str | None:
        """加载超级设备，支持通过序列号或路径查询。

        Args:
            serial: 超级设备序列号。
            super_device_path: 设备路径（用于解析序列号）。

        Returns:
            超级设备 JSON 字符串，未找到时返回 None。
        """
        if serial is None and super_device_path is not None:
            serial = get_serial(super_device_path)
        if serial is None:
            return None
        sd = self.super_device_repository.get_super_device(serial)
        return sd.to_json() if sd else None

    def list_super_devices(self) -> list[str]:
        """列出所有已注册超级设备的 JSON 字符串列表。

        Returns:
            超级设备 JSON 字符串列表。
        """
        return [sd.to_json() for sd in self.super_device_repository.list_super_device()]

    # ── 字段更新 ──────────────────────────────────────────────────

    def set_name(self, serial: str, name: str) -> tuple[str, str]:
        """更新超级设备名称。

        Args:
            serial: 超级设备序列号。
            name: 新名称。

        Returns:
            tuple[str, str]: (旧值, 新值)。
        """
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = sd.name
        self.super_device_repository.update_super_device(serial, name=name)
        log_event(SuperDeviceFieldUpdated(serial, "name", old, name))
        return (old, name)

    def set_sdtype(self, serial: str, sdtype: str) -> tuple[str, str]:
        """更新超级设备类型。

        Args:
            serial: 超级设备序列号。
            sdtype: 新类型。

        Returns:
            tuple[str, str]: (旧值, 新值)。
        """
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = sd.sdtype
        self.super_device_repository.update_super_device(serial, sdtype=sdtype)
        log_event(SuperDeviceFieldUpdated(serial, "sdtype", old, sdtype))
        return (old, sdtype)

    def set_state(self, serial: str, state: SuperDeviceState) -> tuple[SuperDeviceState, SuperDeviceState]:
        """更新超级设备状态。

        Args:
            serial: 超级设备序列号。
            state: 新状态。

        Returns:
            tuple[SuperDeviceState, SuperDeviceState]: (旧值, 新值)。
        """
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = sd.state
        self.super_device_repository.update_super_device(serial, state=state)
        log_event(SuperDeviceFieldUpdated(serial, "state", old, state))
        return (old, state)

    def set_capacity(self, serial: str, capacity: int) -> tuple[int, int]:
        """更新超级设备容量。

        Args:
            serial: 超级设备序列号。
            capacity: 新容量（字节）。

        Returns:
            tuple[int, int]: (旧值, 新值)。
        """
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = sd.capacity
        self.super_device_repository.update_super_device(serial, capacity=capacity)
        log_event(SuperDeviceFieldUpdated(serial, "capacity", old, capacity))
        return (old, capacity)

    def set_need_all_devices_online(self, serial: str, value: bool) -> tuple[bool, bool]:
        """更新是否需要全部设备同时上线。

        Args:
            serial: 超级设备序列号。
            value: 新值。

        Returns:
            tuple[bool, bool]: (旧值, 新值)。
        """
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = sd.need_all_devices_online
        self.super_device_repository.update_super_device(serial, need_all_devices_online=value)
        log_event(SuperDeviceFieldUpdated(serial, "need_all_devices_online", old, value))
        return (old, value)

    # ── info 操作（JSON 文本） ────────────────────────────────────

    @staticmethod
    def _parse_info(info_str: str | None) -> dict:
        """解析 info JSON 文本为字典。

        Args:
            info_str: JSON 格式的 info 字符串。

        Returns:
            解析后的字典，空值返回空字典。
        """
        if not info_str:
            return {}
        try:
            return json.loads(info_str)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_info(self, serial: str, info: dict) -> tuple[dict, dict]:
        """全量替换 info。

        Args:
            serial: 超级设备序列号。
            info: 新的 info 字典。

        Returns:
            tuple[dict, dict]: (旧info, 新info)。
        """
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = self._parse_info(sd.info)
        new_str = json.dumps(info, ensure_ascii=False)
        self.super_device_repository.update_super_device(serial, info=new_str)
        log_event(SuperDeviceInfoSet(serial, old, info))
        return (old, info)

    def append_info(self, serial: str, data: dict) -> tuple[dict, dict]:
        """合并键值对到现有 info。

        Args:
            serial: 超级设备序列号。
            data: 待合并的键值对字典。

        Returns:
            tuple[dict, dict]: (旧info, 新info)。
        """
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = self._parse_info(sd.info)
        new_info = {**old, **data}
        new_str = json.dumps(new_info, ensure_ascii=False)
        self.super_device_repository.update_super_device(serial, info=new_str)
        for key, new_val in data.items():
            if key in old:
                log_event(SuperDeviceInfoChanged(serial, "replace", key, old[key], new_val))
            else:
                log_event(SuperDeviceInfoChanged(serial, "add", key, None, new_val))
        return (old, new_info)

    def delete_info(self, serial: str, key: str) -> tuple[dict, dict]:
        """从 info 中删除指定键。

        Args:
            serial: 超级设备序列号。
            key: 待删除的键名。

        Returns:
            tuple[dict, dict]: (旧info, 新info)。
        """
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise ValueError(f"super_device {serial} not found")
        old = self._parse_info(sd.info)
        new_info = dict(old)
        old_val = new_info.pop(key, None)
        new_str = json.dumps(new_info, ensure_ascii=False)
        self.super_device_repository.update_super_device(serial, info=new_str)
        if key in old:
            log_event(SuperDeviceInfoChanged(serial, "remove", key, old_val, None))
        return (old, new_info)

    def set_serial(self, old_serial: str, new_serial: str) -> tuple[str, str]:
        """重置超级设备序列号，同步更新关联表。返回 (旧序列号, 新序列号)。"""
        if not self.super_device_repository.is_exist(old_serial):
            raise ValueError(f"super_device {old_serial} not found")
        self.super_device_repository.update_super_device_serial(old_serial, new_serial)
        log_event(SuperDeviceSerialChanged(old_serial=old_serial, new_serial=new_serial))
        return (old_serial, new_serial)

    # ── 子设备管理 ────────────────────────────────────────────────

    def _require_device(self, device_serial: str) -> None:
        """检查设备是否存在，不存在则抛异常。"""
        if self.device_repository is None:
            return
        if not self.device_repository.is_exist(device_serial):
            raise ValueError(f"子设备 {device_serial} 不存在")

    def add_device(self, super_device_serial: str, device_serial: str) -> None:
        """向超级设备新增一个子设备。"""
        sd = self.super_device_repository.get_super_device(super_device_serial)
        if sd is None:
            raise ValueError(f"super_device {super_device_serial} not found")
        self._require_device(device_serial)
        self.super_device_repository.add_device(super_device_serial, device_serial, datetime.now())
        log_event(SuperDeviceDeviceChanged(super_device_serial, old=None, new=device_serial))

    def replace_device(self, super_device_serial: str, old_device_serial: str, new_device_serial: str) -> None:
        """替换超级设备的子设备。"""
        sd = self.super_device_repository.get_super_device(super_device_serial)
        if sd is None:
            raise ValueError(f"super_device {super_device_serial} not found")
        self._require_device(new_device_serial)
        self.super_device_repository.replace_device(
            super_device_serial, old_device_serial, new_device_serial, datetime.now(),
        )
        log_event(SuperDeviceDeviceChanged(super_device_serial, old=old_device_serial, new=new_device_serial))

    def remove_device(self, super_device_serial: str, device_serial: str) -> None:
        """从超级设备移除一个子设备。"""
        sd = self.super_device_repository.get_super_device(super_device_serial)
        if sd is None:
            raise ValueError(f"super_device {super_device_serial} not found")
        self.super_device_repository.remove_device(super_device_serial, device_serial)
        log_event(SuperDeviceDeviceChanged(super_device_serial, old=device_serial, new=None))

    def remove_super_device(self, serial: str) -> None:
        """软删除超级设备（标记 REMOVED）。

        Args:
            serial: 超级设备序列号。

        Raises:
            ValueError: 超级设备不存在。
            SuperDeviceInUseError: 超级设备仍被引用（透传自仓储层）。
        """
        self.super_device_repository.remove_super_device(serial)
        log_event(SuperDeviceRemoved(serial))
