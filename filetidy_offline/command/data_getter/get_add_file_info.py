import core.component.add_file_info as add_file_info

def get_add_file_info():
    add_file=add_file_info.add_file_info()
    add_file._file_path=input("please input file storage path:")
    add_file._storage_volume=input("please tell us which volume do you save your file (default is 0):")
    if add_file._storage_volume=="":
        add_file._storage_volume="0"
    
    return add_file,None