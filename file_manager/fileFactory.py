from file_manager.file import File
class FileFactory:
    @classmethod
    def convert_to_files(cls,file_list:list)->list[File]:
        """
            将从数据库获得的字段列表转换成file列表
        """
        files=[]
        for file in file_list:
            files.append(File(file))

        return files
        