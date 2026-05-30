from domain.storage.file.new_file import NewFile


class FileRegistered:
    def __init__(self, new_file: NewFile):
        self.file = new_file.to_snapshot()
