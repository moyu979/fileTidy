from abc import ABC

from domain.storage.device.base import Device
from domain.storage.file.file_location import file_location
from domain.storage.file.file_source import file_source
from domain.storage.super_device.base import SuperDevice


class file_repository_abc(ABC):
    def __init__(self) -> None:
        pass

    def is_exist(self) -> bool:
        pass

    def reg_file(self, source: file_source,file_location:file_location) -> None:
        pass

