# CHECK: 待检查 - 基础设施 SuperVolume 仓储实现 - 超级卷数据持久化

import logging
from typing import Any

from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.enum import SuperVolumeState
from domain.storage.super_volume.repo import super_volume_repository_abc
from domain.storage.super_volume.structure import SuperVolumeStructure
from infra.persistence.database import session_scope
from infra.persistence.models import RelationState, SuperVolumeModel, SuperVolumeStructureModel

logger = logging.getLogger(__name__)


class SuperVolumeRepository(super_volume_repository_abc):
    """超级卷仓库实现，提供超级卷数据的持久化存储和查询操作。"""

    def __init__(self, session_factory) -> None:
        """
        初始化 SuperVolumeRepository。

        Args:
            session_factory: 用于创建 SQLAlchemy 会话的工厂
        """
        self.session_factory = session_factory
        super().__init__()
        logger.info("SuperVolumeRepository constructed")

    def is_exist(self, super_volume: SuperVolume | str) -> bool:
        """
        判断超级卷是否已存在于数据库中。

        Args:
            super_volume: 超级卷对象或序列号字符串

        Returns:
            存在返回 True，否则返回 False
        """
        if isinstance(super_volume, SuperVolume):
            serial = super_volume.serial
        else:
            serial = super_volume
        with session_scope(self.session_factory) as session:
            return session.query(SuperVolumeModel).filter(SuperVolumeModel.serial == serial).first() is not None

    def reg_super_volume(self, super_volume: SuperVolume) -> None:
        """
        注册一个新的超级卷及其关联的卷结构。

        超级卷主行与其全部子卷关联行在同一事务内提交，
        避免「超级卷已落库、关联行写入失败」产生的脏数据。

        Args:
            super_volume: 要注册的超级卷对象
        """
        super_volume_model = SuperVolumeModel(
            serial=super_volume.serial,
            name=super_volume.name,
            type=super_volume.svtype,
            method=super_volume.method,
            add_time=super_volume.add_time,
            last_check_time=super_volume.last_check_time,
            state=super_volume.state,
            info=super_volume.info,
        )
        structures = []
        for volume_id in super_volume.volumes:
            structure = SuperVolumeStructureModel(
                super_volume_id=super_volume.serial,
                volume_id=volume_id,
                add_time=super_volume.add_time,
                state=RelationState.USING,
                info="",
            )
            structures.append(structure)
        with session_scope(self.session_factory) as session:
            session.add(super_volume_model)
            session.add_all(structures)

    @staticmethod
    def _model_to_dict(model: SuperVolumeModel, volume_ids: list[str]) -> dict[str, Any]:
        """
        将 SuperVolumeModel 转换为字典。

        Args:
            model: SuperVolumeModel 实例
            volume_ids: 关联的卷序列号列表

        Returns:
            包含所有字段的字典
        """
        return {
            "serial": model.serial,
            "name": model.name,
            "type": model.type,
            "method": model.method,
            "add_time": model.add_time,
            "last_check_time": model.last_check_time,
            "state": model.state,
            "info": model.info,
            "volumes": volume_ids,
        }

    def get_super_volume(self, super_volume_serial: str) -> SuperVolume | None:
        """
        根据序列号获取超级卷。

        Args:
            super_volume_serial: 超级卷序列号

        Returns:
            超级卷对象，若不存在则返回 None
        """
        with session_scope(self.session_factory) as session:
            model = session.query(SuperVolumeModel).filter(
                SuperVolumeModel.serial == super_volume_serial
            ).first()
            if model is None:
                return None
            structure_rows = session.query(SuperVolumeStructureModel).filter(
                SuperVolumeStructureModel.super_volume_id == super_volume_serial,
                SuperVolumeStructureModel.state == RelationState.USING,
            ).all()
            volume_ids = [row.volume_id for row in structure_rows]
            data = self._model_to_dict(model, volume_ids)
            return SuperVolume.from_dict(data)

    def list_super_volume(self) -> list[SuperVolume]:
        """
        获取所有已注册的超级卷列表。

        Returns:
            超级卷对象列表
        """
        with session_scope(self.session_factory) as session:
            models = session.query(SuperVolumeModel).all()
            result = []
            for model in models:
                structure_rows = session.query(SuperVolumeStructureModel).filter(
                    SuperVolumeStructureModel.super_volume_id == model.serial,
                    SuperVolumeStructureModel.state == RelationState.USING,
                ).all()
                volume_ids = [row.volume_id for row in structure_rows]
                data = self._model_to_dict(model, volume_ids)
                result.append(SuperVolume.from_dict(data))
            return result

    def add_volumes(
        self,
        structures: list[SuperVolumeStructure],
    ) -> None:
        """
        批量添加卷到超级卷的关联结构中。

        添加前校验超级卷存在，且子卷尚未被任何超级卷关联（含 UNUSED，
        因为 super_volume_structures.volume_id 上有唯一约束）。

        Args:
            structures: 超级卷结构对象列表

        Raises:
            ValueError: 超级卷不存在或子卷已被其他超级卷关联时抛出。
        """
        models = []
        with session_scope(self.session_factory) as session:
            for st in structures:
                parent = session.query(SuperVolumeModel).filter(
                    SuperVolumeModel.serial == st.super_volume_serial
                ).first()
                if parent is None:
                    raise ValueError(f"超级卷 {st.super_volume_serial} 不存在")
                existing = session.query(SuperVolumeStructureModel).filter(
                    SuperVolumeStructureModel.volume_id == st.volume_id
                ).first()
                if existing is not None:
                    raise ValueError(
                        f"卷 {st.volume_id} 已属于超级卷 {existing.super_volume_id}，无法重复添加"
                    )
                model = SuperVolumeStructureModel(
                    super_volume_id=st.super_volume_serial,
                    volume_id=st.volume_id,
                    add_time=st.add_time,
                    state=st.state,
                    info=st.info,
                )
                models.append(model)
            session.add_all(models)

    # 领域字段名 → 模型列名 映射
    _field_mapping = {
        "svtype": "type",
    }

    def update_super_volume(self, serial: str, **fields) -> None:
        """
        更新超级卷的指定字段。

        Args:
            serial: 超级卷序列号
            **fields: 要更新的字段名和值（支持 svtype 自动映射为 type）

        Raises:
            ValueError: 超级卷不存在
        """
        with session_scope(self.session_factory) as session:
            model = (
                session.query(SuperVolumeModel)
                .filter(SuperVolumeModel.serial == serial)
                .first()
            )
            if model is None:
                raise ValueError(f"super_volume {serial} not found")
            for key, value in fields.items():
                col = self._field_mapping.get(key, key)
                setattr(model, col, value)

    def update_super_volume_serial(self, old_serial: str, new_serial: str) -> None:
        """
        重置超级卷序列号，同步更新关联表中的外键引用。

        super_volumes.serial 是主键，被 super_volume_structures.super_volume_id
        外键引用。因不能直接删除被引用的旧主键行，采用
        「旧行临时改名腾出唯一 name → 以 new_serial 复制新主键行 → 迁移引用
        → 再删旧行」的方式（name 列有唯一约束，复制期间旧行必须先让名）。

        Args:
            old_serial: 原超级卷序列号
            new_serial: 新超级卷序列号

        Raises:
            ValueError: 原超级卷不存在
        """
        with session_scope(self.session_factory) as session:
            row = (
                session.query(SuperVolumeModel)
                .filter(SuperVolumeModel.serial == old_serial)
                .first()
            )
            if row is None:
                raise ValueError(f"super_volume {old_serial} not found")
            if old_serial == new_serial:
                return

            # 1. 旧行临时改名，腾出唯一 name 给新行
            original_name = row.name
            row.name = f"{original_name}__renaming__{old_serial}"
            session.flush()

            # 2. 以 new_serial 复制主键行（先让新主键存在，FK 才能指向它）
            new_row = SuperVolumeModel(
                serial=new_serial,
                name=original_name,
                type=row.type,
                method=row.method,
                add_time=row.add_time,
                last_check_time=row.last_check_time,
                state=row.state,
                info=row.info,
            )
            session.add(new_row)
            session.flush()

            # 3. 迁移关联表：super_volume_id old → new
            session.query(SuperVolumeStructureModel).filter(
                SuperVolumeStructureModel.super_volume_id == old_serial
            ).update({"super_volume_id": new_serial})

            # 4. 删除旧主键行
            session.delete(row)

    def remove_volumes(
        self,
        super_volume_serial: str,
        volume_ids: list[str],
    ) -> None:
        """
        从超级卷移除一批子卷（将 USING 关联标记为 UNUSED）。

        Args:
            super_volume_serial: 超级卷序列号
            volume_ids: 待移除的子卷序列号列表

        Raises:
            ValueError: 超级卷不存在，或存在非 USING 成员卷时抛出（不部分更新）。
        """
        with session_scope(self.session_factory) as session:
            parent = session.query(SuperVolumeModel).filter(
                SuperVolumeModel.serial == super_volume_serial
            ).first()
            if parent is None:
                raise ValueError(f"超级卷 {super_volume_serial} 不存在")

            rows = []
            missing = []
            for volume_id in volume_ids:
                row = session.query(SuperVolumeStructureModel).filter(
                    SuperVolumeStructureModel.super_volume_id == super_volume_serial,
                    SuperVolumeStructureModel.volume_id == volume_id,
                    SuperVolumeStructureModel.state == RelationState.USING,
                ).first()
                if row is None:
                    missing.append(volume_id)
                else:
                    rows.append(row)
            if missing:
                raise ValueError(
                    f"卷 {'、'.join(missing)} 不是超级卷 {super_volume_serial} 的 USING 成员，无法移除"
                )
            for row in rows:
                row.state = RelationState.UNUSED

    def remove_super_volume(self, serial: str) -> None:
        """
        将超级卷标记为 REMOVED（软删除），并释放其 USING 子卷关联。

        Args:
            serial: 超级卷序列号

        Raises:
            ValueError: 超级卷不存在
        """
        with session_scope(self.session_factory) as session:
            model = (
                session.query(SuperVolumeModel)
                .filter(SuperVolumeModel.serial == serial)
                .first()
            )
            if model is None:
                raise ValueError(f"super_volume {serial} not found")

            session.query(SuperVolumeStructureModel).filter(
                SuperVolumeStructureModel.super_volume_id == serial,
                SuperVolumeStructureModel.state == RelationState.USING,
            ).update({"state": RelationState.UNUSED})
            model.state = SuperVolumeState.REMOVED
