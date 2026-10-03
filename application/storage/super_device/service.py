# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: 待检查 - 应用层 SuperDevice 服务 - 超级设备业务用例编排

from datetime import datetime
import json
import logging

from domain.common.json_utils import parse_json_object
from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.events import (
    SuperDeviceDeviceChanged,
    SuperDeviceFieldUpdated,
    SuperDeviceInfoChanged,
    SuperDeviceInfoSet,
    SuperDeviceRegistered,
    SuperDeviceRemoved,
    SuperDeviceRevived,
    SuperDeviceSerialChanged,
)
from infra.operation_log.operation_log import log_event
from domain.storage.super_device.enum import SuperDeviceState
from domain.storage.super_device.errors import (
    SubDeviceNotFoundError,
    SuperDeviceAlreadyRegisteredError,
    SuperDeviceAlreadyRemovedError,
    SuperDeviceNotFoundError,
)
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
            ValueError: 超级设备已存在；或已存在但处于 REMOVED
                （需先调用 revive_super_device 复活，而不是重新登记）。
        """
        # 判定与分类都已下沉到仓储：撞 REMOVED 行抛 SuperDeviceAlreadyRemovedError，
        # 撞活跃行抛 SuperDeviceAlreadyRegisteredError。本层只负责把事实翻译成给用户的措辞
        # —— 提示里点名 revive_super_device 属应用层编排，不应由仓储说出口。
        try:
            self.super_device_repository.reg_super_device(super_device)
        except SuperDeviceAlreadyRemovedError as e:
            raise ValueError(
                f"super_device {e.serial} 已被移除（REMOVED），"
                f"如要重新启用请先调用 revive_super_device"
            ) from None
        except SuperDeviceAlreadyRegisteredError as e:
            raise ValueError(f"super_device {e.serial} already exists") from None
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
            raise SuperDeviceNotFoundError(serial)
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
            raise SuperDeviceNotFoundError(serial)
        old = sd.sdtype
        self.super_device_repository.update_super_device(serial, sdtype=sdtype)
        log_event(SuperDeviceFieldUpdated(serial, "sdtype", old, sdtype))
        return (old, sdtype)

    # TODO(P1): set_state 目前能直接把超级设备改成 REMOVED，**绕过 remove_super_device 的引用校验**
    #   （remove_super_device 要求：无被层叠的 USING 子项关联、无未移除的卷）。
    #   后果：一台正被其它超级设备层叠引用、或其上仍有卷的超级设备可以被静默标成 REMOVED，
    #   破坏引用不变式。收口方向（未定稿）：① set_state 拒绝 REMOVED，强制改走
    #   remove_super_device；② 或在 set_state 内部复用 remove_super_device 的那套校验。
    #   注意：仓储层已禁止 update_super_device 写入 REMOVED，因此 set_state(REMOVED)
    #   现在会直接报错（相当于先行收口了路径 ①）；软删除走 remove_super_device，
    #   复活走 revive_super_device。本方法自身的收口整理仍待办。
    def set_state(self, serial: str, state: SuperDeviceState) -> tuple[SuperDeviceState, SuperDeviceState]:
        """更新超级设备状态。

        注意：本方法不校验超级设备是否被引用，因此**不应**用它把超级设备置为 REMOVED；
        软删除请走 `remove_super_device`（带着引用校验）。详见上方 TODO。

        Args:
            serial: 超级设备序列号。
            state: 新状态。

        Returns:
            tuple[SuperDeviceState, SuperDeviceState]: (旧值, 新值)。
        """
        sd = self.super_device_repository.get_super_device(serial)
        if sd is None:
            raise SuperDeviceNotFoundError(serial)
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
            raise SuperDeviceNotFoundError(serial)
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
            raise SuperDeviceNotFoundError(serial)
        old = sd.need_all_devices_online
        self.super_device_repository.update_super_device(serial, need_all_devices_online=value)
        log_event(SuperDeviceFieldUpdated(serial, "need_all_devices_online", old, value))
        return (old, value)

    # ── info 操作（JSON 文本） ────────────────────────────────────

    @staticmethod
    def _parse_info(info_str: str | None) -> dict:
        """解析 info JSON 文本为字典（薄封装，逻辑见 parse_json_object）。"""
        return parse_json_object(info_str)

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
            raise SuperDeviceNotFoundError(serial)
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
            raise SuperDeviceNotFoundError(serial)
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
            raise SuperDeviceNotFoundError(serial)
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
            raise SuperDeviceNotFoundError(old_serial)
        self.super_device_repository.update_super_device_serial(old_serial, new_serial)
        log_event(SuperDeviceSerialChanged(old_serial=old_serial, new_serial=new_serial))
        return (old_serial, new_serial)

    # ── 子设备管理 ────────────────────────────────────────────────

    def _require_device(self, device_serial: str) -> None:
        """检查设备是否存在，不存在则抛异常。"""
        if self.device_repository is None:
            return
        if not self.device_repository.is_exist(device_serial):
            raise SubDeviceNotFoundError(device_serial)

    def add_device(self, super_device_serial: str, device_serial: str) -> None:
        """向超级设备新增一个子设备。"""
        sd = self.super_device_repository.get_super_device(super_device_serial)
        if sd is None:
            raise SuperDeviceNotFoundError(super_device_serial)
        self._require_device(device_serial)
        self.super_device_repository.add_device(super_device_serial, device_serial, datetime.now())
        log_event(SuperDeviceDeviceChanged(super_device_serial, old=None, new=device_serial))

    def replace_device(self, super_device_serial: str, old_device_serial: str, new_device_serial: str) -> None:
        """替换超级设备的子设备。"""
        sd = self.super_device_repository.get_super_device(super_device_serial)
        if sd is None:
            raise SuperDeviceNotFoundError(super_device_serial)
        self._require_device(new_device_serial)
        self.super_device_repository.replace_device(
            super_device_serial, old_device_serial, new_device_serial, datetime.now(),
        )
        log_event(SuperDeviceDeviceChanged(super_device_serial, old=old_device_serial, new=new_device_serial))

    # TODO(P1): 「摘子项」功能暂缓（仓储/ABC 已同步停用）。
    #   恢复时取消下面注释，并同步恢复 CLI do_remove_device 与相关测试。
    #
    # def remove_device(self, super_device_serial: str, device_serial: str) -> None:
    #     """从超级设备移除一个子设备。"""
    #     sd = self.super_device_repository.get_super_device(super_device_serial)
    #     if sd is None:
    #         raise SuperDeviceNotFoundError(super_device_serial)
    #     self.super_device_repository.remove_device(super_device_serial, device_serial)
    #     log_event(SuperDeviceDeviceChanged(super_device_serial, old=device_serial, new=None))

    def remove_super_device(self, serial: str) -> None:
        """软删除超级设备（标记 REMOVED）。

        事件携"删除前"快照，故先读一次原始实体（exclude_removed=False）再落库删除。

        Args:
            serial: 超级设备序列号。

        Raises:
            SuperDeviceNotFoundError: 超级设备不存在。
            SuperDeviceAlreadyRemovedError: 超级设备已处于 REMOVED（不可重复移除，透传自仓储层）。
            SuperDeviceInUseError: 超级设备仍被引用（透传自仓储层）。
        """
        super_device = self.super_device_repository.get_super_device(
            serial, exclude_removed=False
        )
        if super_device is None:
            raise SuperDeviceNotFoundError(serial)
        self.super_device_repository.remove_super_device(serial)
        log_event(SuperDeviceRemoved(super_device))

    def revive_super_device(self, serial: str) -> None:
        """复活已移除（REMOVED）的超级设备（state 置回 UNKNOWN，拓扑一并恢复）。

        删除时释放的子项会被重新挂回；若某个子项已被其它超级设备占用，
        则整个复活流程回滚（透传仓储层的领域异常）。

        Args:
            serial: 超级设备序列号。

        Raises:
            SuperDeviceNotFoundError: 超级设备不存在（透传自仓储层）。
            SuperDeviceNotRemovedError: 超级设备未处于 REMOVED（无需复活，透传自仓储层）。
            SubDeviceInUseError: 待恢复的子项已被其它超级设备占用（透传自仓储层）。
        """
        self.super_device_repository.revive_super_device(serial)
        log_event(SuperDeviceRevived(serial))
