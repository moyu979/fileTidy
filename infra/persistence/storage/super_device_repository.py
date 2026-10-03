import logging
from typing import Any

from domain.common.json_utils import parse_json_object
from domain.storage.device.enum import UNAVAILABLE_DEVICE_STATES
from domain.storage.super_device.base import SuperDevice
from domain.storage.super_device.enum import (
    SuperDeviceRelationState,
    SuperDeviceState,
    UNAVAILABLE_SUPER_DEVICE_STATES,
)
from domain.storage.super_device.errors import (
    SubDeviceInUseError,
    SubDeviceNotFoundError,
    SubDeviceUnavailableError,
    SuperDeviceAlreadyRegisteredError,
    SuperDeviceAlreadyRemovedError,
    SuperDeviceInUseError,
    SuperDeviceNotFoundError,
    SuperDeviceNotRemovedError,
)
from domain.storage.volume.enum import VolumeState
from domain.storage.super_device.repo import SuperDeviceRepositoryABC
from infra.persistence._enum_utils import coerce_enum
from infra.persistence._model_utils import updatable_fields
from infra.persistence.database import session_scope
from infra.persistence.models import (
    DeviceModel,
    SuperDeviceModel,
    SuperDeviceStructureModel,
    VolumeModel,
)

logger = logging.getLogger(__name__)


def _resolve_sub(session, sub_id: str) -> tuple[str, Any] | None:
    """
    解析子项类型：是 device 还是 super_device（支持层叠）。

    Args:
        session: SQLAlchemy 会话
        sub_id: 子项序列号

    Returns:
        (kind, model) 元组；kind 为 "device" 或 "super_device"，查不到返回 None
    """
    device = (
        session.query(DeviceModel)
        .filter(DeviceModel.serial == sub_id)
        .first()
    )
    if device is not None:
        return "device", device
    super_device = (
        session.query(SuperDeviceModel)
        .filter(SuperDeviceModel.serial == sub_id)
        .first()
    )
    if super_device is not None:
        return "super_device", super_device
    return None


def _ensure_sub_available(session, sub_id: str) -> None:
    """
    校验子项可挂载：独占（未被其它超级设备以 USING 占用）+ 实体可用（非 REMOVED/FAULT）。

    Args:
        session: SQLAlchemy 会话
        sub_id: 子项序列号

    Raises:
        SubDeviceInUseError: 子项已被其它超级设备以 USING 占用
        SubDeviceNotFoundError: 子项既不是 device 也不是 super_device
        SubDeviceUnavailableError: 子项实体处于 REMOVED/FAULT 不可用状态
    """
    holder = (
        session.query(SuperDeviceStructureModel)
        .filter(
            SuperDeviceStructureModel.sub_device_id == sub_id,
            SuperDeviceStructureModel.state == SuperDeviceRelationState.USING,
        )
        .first()
    )
    if holder is not None:
        raise SubDeviceInUseError(sub_id, holder.super_device_id)

    resolved = _resolve_sub(session, sub_id)
    if resolved is None:
        raise SubDeviceNotFoundError(sub_id)
    kind, model = resolved
    if kind == "device" and model.state in UNAVAILABLE_DEVICE_STATES:
        raise SubDeviceUnavailableError(sub_id, model.state)
    if kind == "super_device" and model.state in UNAVAILABLE_SUPER_DEVICE_STATES:
        raise SubDeviceUnavailableError(sub_id, model.state)


class SuperDeviceRepository(SuperDeviceRepositoryABC):
    """超级设备仓库实现，提供超级设备数据的持久化存储和查询操作。"""

    def __init__(self, session_factory) -> None:
        """
        初始化 SuperDeviceRepository。

        Args:
            session_factory: 用于创建 SQLAlchemy 会话的工厂
        """
        self.session_factory = session_factory
        super().__init__()
        logger.info("SuperDeviceRepository constructed")
    def is_exist(self, super_device: SuperDevice | str) -> bool:
        """
        判断超级设备是否已存在于数据库中。

        Args:
            super_device: 超级设备对象或序列号字符串

        Returns:
            存在返回 True，否则返回 False
        """
        if isinstance(super_device, SuperDevice):
            serial = super_device.serial
        else:
            serial = super_device
        with session_scope(self.session_factory) as session:
            return session.query(SuperDeviceModel).filter(SuperDeviceModel.serial == serial).first() is not None
    def reg_super_device(self, super_device: SuperDevice) -> None:
        """
        注册一个新的超级设备及其子设备关联关系。

        超级设备主行与其所有子设备关联行在同一事务内提交，
        避免「超级设备已落库、关联行写入失败」产生的脏数据。

        Args:
            super_device: 要注册的超级设备对象

        Raises:
            SuperDeviceAlreadyRegisteredError: 该 serial 已被一条非 REMOVED 的行占用
            SuperDeviceAlreadyRemovedError: 该 serial 被一条 REMOVED（软删除）行占位，需先复活
            SubDeviceInUseError / SubDeviceNotFoundError / SubDeviceUnavailableError:
                任一子项不满足独占 / 存在 / 可用
        """
        super_device_model = SuperDeviceModel(
            serial=super_device.serial,
            name=super_device.name,
            sdtype=super_device.sdtype,
            need_all_devices_online=super_device.need_all_devices_online,
            add_time=super_device.add_time,
            last_check_time=super_device.last_check_time,
            state=coerce_enum(SuperDeviceState, super_device.state),
            capacity=super_device.capacity,
            info=super_device.info,
        )
        devices = []
        # TODO(P2): 子项列表含重复序列号时（如 devices=["D1","D1"]）会撞结构表复合主键
        #   (super_device_id, sub_device_id) 抛裸 IntegrityError —— 暂缓，当前无用例触发。
        #   single 变体有「恰好 1 个」断言间接挡住，但 raidz 无去重、仓储也不校验 → 可达。
        #   修复方向：落库前对 devices 去重，或对重复项抛明确的领域异常。
        for device in super_device.devices:
            super_device_structure_model = SuperDeviceStructureModel(
                super_device_id=super_device.serial,
                sub_device_id=device,
                add_time=super_device.add_time,
                state=SuperDeviceRelationState.USING,
                info="",
            )
            devices.append(super_device_structure_model)
        # 超级设备主行 + 全部关联行：同一个事务，保证原子性（session_scope 退出时自动 commit）
        with session_scope(self.session_factory) as session:
            # 唯一性预检：serial 是主键，任何已存在的行（含 REMOVED）都算占用。
            # 在这里判定（而不是让 INSERT 撞 PK），使调用方——含绕过 service 的——都能拿到
            # 结构化领域异常而非裸 IntegrityError。
            existing = (
                session.query(SuperDeviceModel)
                .filter(SuperDeviceModel.serial == super_device.serial)
                .first()
            )
            if existing is not None:
                # 分类就在仓储完成：REMOVED 行占位 与 活跃占用 是互斥的两种事实，
                # 各给一个异常类型，上层不必再自己看 state 分流。
                if existing.state == SuperDeviceState.REMOVED:
                    raise SuperDeviceAlreadyRemovedError(super_device.serial)
                raise SuperDeviceAlreadyRegisteredError(
                    super_device.serial, state=existing.state
                )
            # 挂载前校验每个子项：独占（未被其它超级设备 USING 占用）+ 实体可用
            for sub_id in super_device.devices:
                _ensure_sub_available(session, sub_id)
            session.add(super_device_model)
            session.add_all(devices)
            # 显式提交（与 device/volume 仓储一致）；session_scope 退出时的提交为幂等兜底
            session.commit()

    @staticmethod
    def _model_to_dict(model: SuperDeviceModel, device_ids: list[str]) -> dict[str, Any]:
        """
        将 SuperDeviceModel 转换为字典。

        Args:
            model: SuperDeviceModel 实例
            device_ids: 子设备序列号列表

        Returns:
            包含所有字段的字典
        """
        return {
            "serial": model.serial,
            "name": model.name,
            "sdtype": model.sdtype,
            "need_all_devices_online": model.need_all_devices_online,
            "add_time": model.add_time,
            "last_check_time": model.last_check_time,
            "state": model.state,
            "capacity": model.capacity,
            "info": model.info,
            "devices": device_ids,
        }

    def get_super_device(
        self, super_device_serial: str, exclude_removed: bool = True
    ) -> SuperDevice | None:
        """
        根据序列号获取超级设备。

        Args:
            super_device_serial: 超级设备序列号
            exclude_removed: 为 True（默认）时，已移除（REMOVED）的超级设备视为不存在

        Returns:
            超级设备对象，若不存在则返回 None
        """
        with session_scope(self.session_factory) as session:
            query = session.query(SuperDeviceModel).filter(
                SuperDeviceModel.serial == super_device_serial
            )
            if exclude_removed:
                query = query.filter(SuperDeviceModel.state != SuperDeviceState.REMOVED)
            model = query.first()
            if model is None:
                return None
            structure_rows = session.query(SuperDeviceStructureModel).filter(
                SuperDeviceStructureModel.super_device_id == super_device_serial,
                SuperDeviceStructureModel.state == SuperDeviceRelationState.USING,
            ).all()
            device_ids = [row.sub_device_id for row in structure_rows]
            data = self._model_to_dict(model, device_ids)
            return SuperDevice.from_dict(data)


    def list_super_device(self, exclude_removed: bool = True) -> list[SuperDevice]:
        """
        获取已注册的超级设备列表。

        Args:
            exclude_removed: 为 True（默认）时排除已移除（REMOVED）的超级设备。

        Returns:
            超级设备对象列表
        """
        with session_scope(self.session_factory) as session:
            query = session.query(SuperDeviceModel)
            if exclude_removed:
                query = query.filter(SuperDeviceModel.state != SuperDeviceState.REMOVED)
            models = query.all()
            result = []
            for model in models:
                structure_rows = session.query(SuperDeviceStructureModel).filter(
                    SuperDeviceStructureModel.super_device_id == model.serial,
                    SuperDeviceStructureModel.state == SuperDeviceRelationState.USING,
                ).all()
                device_ids = [row.sub_device_id for row in structure_rows]
                data = self._model_to_dict(model, device_ids)
                result.append(SuperDevice.from_dict(data))
            return result

    def update_super_device(self, serial: str, /, **fields) -> None:
        """
        更新超级设备的指定字段。

        值为 None 的字段视为「未提供」，保持原值不变（区别于「清空」）。
        可更新字段自动取自 SuperDeviceModel 的列（主键 serial 除外），未知字段会报错，
        避免拼错键名时静默无效。

        Note:
            `serial` 是位置参数（positional-only），不能作为关键字传入；序列号不可经本方法
            修改（会直接报错），改名请走 `update_super_device_serial`（会同步迁移关联表引用）。

        Args:
            serial: 超级设备序列号（位置参数）
            **fields: 要更新的字段名和值（领域字段名即模型属性名）；
                None 表示不修改该字段

        Raises:
            SuperDeviceNotFoundError: 超级设备不存在
            ValueError: 含未知字段；或试图修改 serial（须走 update_super_device_serial）；
                或把 state 改为 REMOVED（软删除必须走 remove_super_device，以免绕过引用校验）
        """
        with session_scope(self.session_factory) as session:
            model = (
                session.query(SuperDeviceModel)
                .filter(SuperDeviceModel.serial == serial)
                .first()
            )
            if model is None:
                raise SuperDeviceNotFoundError(serial)
            allowed = updatable_fields(SuperDeviceModel)
            for key, value in fields.items():
                if key == "serial":
                    # 改名必须走 update_super_device_serial：它会同步迁移父/子关联与卷归属，
                    # 通用通道不会。
                    raise ValueError(
                        f"super_device {serial} 不允许通过 update_super_device 修改序列号，"
                        f"请改用 update_super_device_serial（会同步迁移关联表引用）"
                    )
                if key not in allowed:
                    raise ValueError(
                        f"super_device {serial} 不支持更新字段 {key!r}；"
                        f"可更新字段：{', '.join(sorted(allowed))}"
                    )
                if value is None:  # None = 未提供该字段 → 保持原样
                    continue
                if key == "state":
                    value = coerce_enum(SuperDeviceState, value)
                    if value is SuperDeviceState.REMOVED:
                        raise ValueError(
                            f"super_device {serial} 不允许通过 update_super_device 置为 REMOVED，"
                            f"请改用 remove_super_device（带引用校验）"
                        )
                setattr(model, key, value)
            session.commit()

    def update_super_device_serial(self, old_serial: str, new_serial: str) -> None:
        """
        重置超级设备序列号，同步更新关联表中的外键引用。

        super_devices.serial 是主键，被以下位置引用，需一并迁移：
        - super_device_structures.super_device_id（作为父时的子项关联，有 FK）
        - super_device_structures.sub_device_id（作为子项被层叠引用）
        - volumes.device_id（卷建立在超级设备上）

        因 super_device_structures.super_device_id 有外键指向 super_devices.serial，
        不能像 device 那样 delete→改主键→add（删除旧父行会被 FK 拦），
        改为「先以 new_serial 复制新主键行 → 迁移引用 → 再删旧行」。

        Args:
            old_serial: 原序列号
            new_serial: 新序列号

        Raises:
            SuperDeviceNotFoundError: 原序列号对应的超级设备不存在
            SuperDeviceAlreadyRemovedError: 新序列号被一条 REMOVED（软删除）行占位
            SuperDeviceAlreadyRegisteredError: 新序列号已被一条非 REMOVED 的行占用
        """
        with session_scope(self.session_factory) as session:
            row = (
                session.query(SuperDeviceModel)
                .filter(SuperDeviceModel.serial == old_serial)
                .first()
            )
            if row is None:
                raise SuperDeviceNotFoundError(old_serial)
            if old_serial == new_serial:
                return

            # 预检：目标 serial 是否已被占用。serial 是主键，任何已存在的行（含 REMOVED 墓碑）
            # 都算占用；不预检的话，下面复制新主键行会在 flush 时撞 PK 抛裸 IntegrityError。
            # 分类与 reg_super_device 同口径：墓碑 → AlreadyRemoved，活跃 → AlreadyRegistered。
            conflict = (
                session.query(SuperDeviceModel)
                .filter(SuperDeviceModel.serial == new_serial)
                .first()
            )
            if conflict is not None:
                if conflict.state == SuperDeviceState.REMOVED:
                    raise SuperDeviceAlreadyRemovedError(new_serial)
                raise SuperDeviceAlreadyRegisteredError(new_serial, state=conflict.state)

            # 1. 以 new_serial 复制主键行（先让新主键存在，FK 才能指向它）
            new_row = SuperDeviceModel(
                serial=new_serial,
                name=row.name,
                sdtype=row.sdtype,
                need_all_devices_online=row.need_all_devices_online,
                add_time=row.add_time,
                last_check_time=row.last_check_time,
                state=row.state,
                capacity=row.capacity,
                info=row.info,
            )
            session.add(new_row)
            session.flush()

            # 2. 迁移引用表：old → new
            session.query(SuperDeviceStructureModel).filter(
                SuperDeviceStructureModel.super_device_id == old_serial
            ).update({"super_device_id": new_serial})
            session.query(SuperDeviceStructureModel).filter(
                SuperDeviceStructureModel.sub_device_id == old_serial
            ).update({"sub_device_id": new_serial})
            session.query(VolumeModel).filter(
                VolumeModel.device_id == old_serial
            ).update({"device_id": new_serial})

            # 3. 删除旧主键行
            session.delete(row)
            session.commit()

    # ── 子设备管理 ────────────────────────────────────────────────

    def add_device(self, super_device_serial: str, device_serial: str, add_time) -> None:
        """
        向超级设备新增一个子设备。

        Args:
            super_device_serial: 超级设备序列号
            device_serial: 子设备序列号
            add_time: 添加时间
        """
        # TODO(P2): 复用「已退役」子项会撞复合主键（裸 IntegrityError）—— 暂缓，当前无用例触发。
        #   现象：在**同一个父级**下使用一个曾退役的子项序列号时，INSERT (super_device_id, sub_device_id)
        #   撞 (父,子) 复合主键。例：SD1 先 replace D1→D3（(SD1,D1) 转 REPLACED 但行保留），
        #   之后 replace D2→D1 或 add_device(SD1, D1) 就会失败。
        #   根因：_ensure_sub_available 判「占用」只看 state == USING，而写入是直接 INSERT 新行；
        #   但「换盘 / 父行软删」都只改 state、不删行（REPLACED / SUPER_DEVICE_REMOVED），
        #   旧行永久占着这对主键 —— 校验口径与写入口径不一致。
        #   修复方向：改 upsert —— 同一 (父,子) 已有历史行则重激活为 USING（刷新 add_time/info），
        #   否则才新建；若确定「退役子项不得回到同一父级」，则退化为先预检并抛明确领域异常。
        #   影响面：add_device 与 replace_device 两条 INSERT 路径（见下方 replace_device 的引用）。
        # TODO(P2): 嵌套层叠缺环检测 —— 暂缓，当前无用例触发。
        #   场景：超级设备支持层叠（子项可为另一个超级设备），但挂载只校验子项存在/可用/独占，
        #   不做祖先遍历 → 可构造环：add_device(SD1, SD2) 之后再 add_device(SD2, SD1) 均成功。
        #   后果：任何递归遍历拓扑（容量汇总 / 一致性校验 / 未来加锁）可能无限循环。
        #   修复方向：在挂载路径（本方法；replace_device 的新子项同样可为超级设备）中，
        #   从待挂子项向上追溯祖先，命中当前父（或子项自身）时拒绝并抛领域异常。
        with session_scope(self.session_factory) as session:
            _ensure_sub_available(session, device_serial)
            row = SuperDeviceStructureModel(
                super_device_id=super_device_serial,
                sub_device_id=device_serial,
                add_time=add_time,
                state=SuperDeviceRelationState.USING,
                info="",
            )
            session.add(row)
            session.commit()

    def replace_device(
        self, super_device_serial: str, old_device_serial: str,
        new_device_serial: str, add_time,
    ) -> None:
        """
        替换超级设备中的子设备（将旧设备标记为 REPLACED，添加新设备映射）。

        Args:
            super_device_serial: 超级设备序列号
            old_device_serial: 被替换的子设备序列号
            new_device_serial: 新子设备序列号
            add_time: 添加时间

        Raises:
            ValueError: 旧设备未在超级设备中找到
        """
        with session_scope(self.session_factory) as session:
            # 0. 校验新子项可挂载（独占 + 实体可用），fail-fast
            _ensure_sub_available(session, new_device_serial)
            # 1. 查找旧映射，标记 REPLACED（换盘退役；不可随复活恢复）
            old_row = (
                session.query(SuperDeviceStructureModel)
                .filter(
                    SuperDeviceStructureModel.super_device_id == super_device_serial,
                    SuperDeviceStructureModel.sub_device_id == old_device_serial,
                    SuperDeviceStructureModel.state == SuperDeviceRelationState.USING,
                )
                .first()
            )
            if old_row is None:
                raise ValueError(
                    f"device {old_device_serial} not found in super_device {super_device_serial}"
                )
            old_row.state = SuperDeviceRelationState.REPLACED

            # 2. 旧映射的 info 中记录 replaced_by
            old_info = parse_json_object(old_row.info)
            old_info["replaced_by"] = new_device_serial
            import json
            old_row.info = json.dumps(old_info, ensure_ascii=False)

            # 3. 新增新设备映射
            #    TODO(P2): 与 add_device 同源 —— 若 (本父, new_device_serial) 已存在退役行，
            #    此处 INSERT 会撞复合主键抛裸 IntegrityError（详见 add_device 上方注释）。
            new_row = SuperDeviceStructureModel(
                super_device_id=super_device_serial,
                sub_device_id=new_device_serial,
                add_time=add_time,
                state=SuperDeviceRelationState.USING,
                info="",
            )
            session.add(new_row)
            session.commit()

    # TODO(P1): 「摘子项」功能暂缓 —— **致命问题**：当前没有配套的迁移逻辑，忽略本功能
    #   直接摘除子项会导致阵列崩坏（换盘 / 降级重建等数据迁移尚未实现）。
    #   在安全迁移方案落地前，不得启用本方法。
    #   恢复时：取消下面注释，并重新评估 SingleSuperDevice 的子项数约束
    #   （摘子项会造出「非 REMOVED 且 0 子项」的 single，而该变体目前只放行 REMOVED 的 0 子项）。
    #
    # def remove_device(self, super_device_serial: str, device_serial: str) -> None:
    #     """
    #     从超级设备移除一个子设备（将其状态标记为 UNUSED）。
    #
    #     Args:
    #         super_device_serial: 超级设备序列号
    #         device_serial: 要移除的子设备序列号
    #
    #     Raises:
    #         ValueError: 设备未在超级设备中找到
    #     """
    #     with session_scope(self.session_factory) as session:
    #         row = (
    #             session.query(SuperDeviceStructureModel)
    #             .filter(
    #                 SuperDeviceStructureModel.super_device_id == super_device_serial,
    #                 SuperDeviceStructureModel.sub_device_id == device_serial,
    #                 SuperDeviceStructureModel.state == SuperDeviceRelationState.USING,
    #             )
    #             .first()
    #         )
    #         if row is None:
    #             raise ValueError(
    #                 f"device {device_serial} not found in super_device {super_device_serial}"
    #             )
    #         # TODO(P1): UNUSED 已随枚举拆分移除，重启「摘子项」时需先定用哪个状态
    #         row.state = SuperDeviceRelationState.SUPER_DEVICE_REMOVED  # 占位，非最终语义
    #         session.commit()

    def remove_super_device(self, serial: str) -> None:
        """
        将超级设备标记为 REMOVED（软删除），保留记录与关联完整性。

        移除前检查超级设备是否仍被引用：
        - super_device_structures 中 sub_device_id == serial 且 state == USING（被层叠）
        - volumes 中 device_id == serial 且 state != REMOVED（卷建立在超级设备上）
        存在任意引用则抛出 SuperDeviceInUseError，不执行移除（事务回滚）。

        移除成功时，会把本超级设备名下的子项关联行（super_device_id == serial 且
        state == USING）一并置为 SUPER_DEVICE_REMOVED，释放这些子项（与 remove_device 同口径）；
        否则父行软删后，子项会因 `_ensure_sub_available` 只按 USING 判占用而被永久锁死。
        用独立状态（而非 UNUSED）是为了与「换盘退役」区分：只有本方法释放的关联行
        会被 `revive_super_device` 恢复，不会把换掉的盘复活。

        Note:
            置为 REMOVED 只能走本方法，不要用 `update_super_device(state=REMOVED)` ——
            仓储层会直接拒绝，那样会绕过上面的引用校验。
            被移除的超级设备可经 `revive_super_device` 复活（state 置回 UNKNOWN，拓扑一并恢复）。

        Args:
            serial: 超级设备序列号

        Raises:
            SuperDeviceNotFoundError: 超级设备不存在
            SuperDeviceAlreadyRemovedError: 超级设备已处于 REMOVED（不可重复移除）
            SuperDeviceInUseError: 超级设备仍被引用
        """
        with session_scope(self.session_factory) as session:
            model = (
                session.query(SuperDeviceModel)
                .filter(SuperDeviceModel.serial == serial)
                .first()
            )
            if model is None:
                raise SuperDeviceNotFoundError(serial)
            if model.state == SuperDeviceState.REMOVED:
                raise SuperDeviceAlreadyRemovedError(serial)

            super_using = (
                session.query(SuperDeviceStructureModel)
                .filter(
                    SuperDeviceStructureModel.sub_device_id == serial,
                    SuperDeviceStructureModel.state == SuperDeviceRelationState.USING,
                )
                .count()
            )
            volumes = (
                session.query(VolumeModel)
                .filter(
                    VolumeModel.device_id == serial,
                    VolumeModel.state != VolumeState.REMOVED,
                )
                .count()
            )
            if super_using or volumes:
                raise SuperDeviceInUseError(
                    serial,
                    super_device_using=super_using,
                    volumes=volumes,
                )

            # 释放本超级设备名下的子项关联行（USING → SUPER_DEVICE_REMOVED）：
            # 父行软删后这些子项不应再被视为「被占用」，否则会被永久锁死
            # （_ensure_sub_available 只按 state == USING 判占用，不看父行是否已 REMOVED）。
            # 用独立状态而非 UNUSED，是为了与「换盘退役（REPLACED）」区分，
            # 使 revive_super_device 能精确恢复本方法释放的关联，而不误复活换掉的盘。
            session.query(SuperDeviceStructureModel).filter(
                SuperDeviceStructureModel.super_device_id == serial,
                SuperDeviceStructureModel.state == SuperDeviceRelationState.USING,
            ).update({"state": SuperDeviceRelationState.SUPER_DEVICE_REMOVED})

            model.state = SuperDeviceState.REMOVED
            session.commit()

    def revive_super_device(self, serial: str) -> None:
        """
        复活已移除（REMOVED）的超级设备：原地把 state 置回 UNKNOWN。

        复活是可逆软删除的逆操作：行原地 UPDATE（serial 是主键，不能重新 INSERT），
        其余字段保持删除前的值不变。目标状态为 UNKNOWN（复活 ≠ 立即可用）。

        拓扑一并恢复：把 `remove_super_device` 释放掉的那批子项关联行
        （state == SUPER_DEVICE_REMOVED）重新置回 USING；
        `replace_device` 换下来的旧子项（state == REPLACED）**不**恢复。

        前置校验（任一失败均抛异常，事务整体回滚）：
        - 目标存在、且正处于 REMOVED；
        - **不校验目标自身是否被引用**（见此处的 TODO 注释）；
        - 待恢复的每个子项都未被他处占用且实体可用 → 透传 SubDeviceInUseError /
          SubDeviceUnavailableError / SubDeviceNotFoundError（与挂载同口径）。

        Args:
            serial: 超级设备序列号

        Raises:
            SuperDeviceNotFoundError: 超级设备不存在
            SuperDeviceNotRemovedError: 超级设备未处于 REMOVED（无需复活）
            SubDeviceInUseError: 待恢复的子项已被其它超级设备占用
            SubDeviceUnavailableError: 待恢复的子项实体已 REMOVED / FAULT
        """
        with session_scope(self.session_factory) as session:
            model = (
                session.query(SuperDeviceModel)
                .filter(SuperDeviceModel.serial == serial)
                .first()
            )
            if model is None:
                raise SuperDeviceNotFoundError(serial)
            if model.state != SuperDeviceState.REMOVED:
                raise SuperDeviceNotRemovedError(serial, model.state)

            # 不校验占用（曾抛 SuperDeviceReviveBlockedError）：被引用的超级设备根本进不了
            # REMOVED（`remove_super_device` 用 SuperDeviceInUseError 把关），所以
            # 「REMOVED 且仍被层叠 / 仍挂着卷」只可能来自并发或手工改库，而这类脏状态
            # 恰恰该由复活修复（state 回到 UNKNOWN 后与引用关系自洽），拦下来只会卡死。
            # TODO(P1): 并发仍可能出错 —— remove_super_device 校验通过后、置 REMOVED 之前，
            #   该超级设备被别人层叠为子项 / 建上卷，此时复活会照常成功（库内出现
            #   「非 REMOVED 且被引用」的常规态）。要堵这个窗口应在 remove_super_device 侧
            #   收口（加锁 / 落库前复检），而不是让 revive 拒绝修复。
            # 恢复拓扑：把本超级设备软删时释放的子项（SUPER_DEVICE_REMOVED）逐项挂回 USING。
            # 每一项先做「未被他处占用 + 实体仍在且可用（非 REMOVED/FAULT）」校验；
            # 任一不通过就抛异常，由 session_scope 整体回滚（state 与拓扑都不会被改动）。
            released_rows = (
                session.query(SuperDeviceStructureModel)
                .filter(
                    SuperDeviceStructureModel.super_device_id == serial,
                    SuperDeviceStructureModel.state == SuperDeviceRelationState.SUPER_DEVICE_REMOVED,
                )
                .all()
            )
            for row in released_rows:
                _ensure_sub_available(session, row.sub_device_id)
                row.state = SuperDeviceRelationState.USING

            model.state = SuperDeviceState.UNKNOWN
            session.commit()
