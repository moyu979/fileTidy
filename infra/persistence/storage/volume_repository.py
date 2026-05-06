from domain.storage.volume.base import Volume
from domain.storage.volume.volume_repo import volume_repository_abc
from infra.persistence.database import session_scope
from infra.persistence.models import VolumeModel

class volume_repository(volume_repository_abc):
    def __init__(self,session_factory) -> None:
        self.session_factory = session_factory
        super().__init__()

    def is_exist(self, volume: Volume) -> bool:
        with session_scope(self.session_factory) as session:
            return session.query(VolumeModel).filter(VolumeModel.id == volume.id).first() is not None

