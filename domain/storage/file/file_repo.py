from abc import ABC, abstractmethod

from domain.storage.file.new_file import NewFile


class file_repository_abc(ABC):
    def __init__(self,) -> None:
        pass

    def is_exist(self) -> bool:
        pass

    def reg_file(self, new_file: NewFile) -> None:
        pass

    

