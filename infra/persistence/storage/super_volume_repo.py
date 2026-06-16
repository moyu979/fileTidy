from typing import Any

from domain.storage.super_volume.base import SuperVolume
from domain.storage.super_volume.factory import super_volume_from_dict
from domain.storage.super_volume.repo import super_volume_repository_abc
from domain.storage.super_volume.structure import SuperVolumeStructure
from infra.persistence.database import session_scope
from infra.persistence.models import RelationState, SuperVolumeModel, SuperVolumeStructureModel


class super_Volume_repository(super_volume_repository_abc):
    def __init__(self, session_factory) -> None:
        self.session_factory = session_factory
        super().__init__()

    def is_exist(self, super_volume: SuperVolume | str) -> bool:
        if isinstance(super_volume, SuperVolume):
            serial = super_volume.serial
        else:
            serial = super_volume
        with session_scope(self.session_factory) as session:
            return session.query(SuperVolumeModel).filter(SuperVolumeModel.serial == serial).first() is not None

    def reg_super_volume(self, super_volume: SuperVolume) -> None:
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
        with session_scope(self.session_factory) as session:
            session.add(super_volume_model)
            session.commit()

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
            session.add_all(structures)
            session.commit()

    @staticmethod
    def _model_to_dict(model: SuperVolumeModel, volume_ids: list[str]) -> dict[str, Any]:
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
            return super_volume_from_dict(data)

    def list_super_volume(self) -> list[SuperVolume]:
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
                result.append(super_volume_from_dict(data))
            return result

    def add_volumes(
        self,
        structures: list[SuperVolumeStructure],
    ) -> None:
        models = []
        for st in structures:
            model = SuperVolumeStructureModel(
                super_volume_id=st.super_volume_serial,
                volume_id=st.volume_id,
                add_time=st.add_time,
                state=st.state,
                info=st.info,
            )
            models.append(model)
        with session_scope(self.session_factory) as session:
            session.add_all(models)
            session.commit()