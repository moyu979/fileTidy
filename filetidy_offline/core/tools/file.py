import os
def get_size(path):
    file_size = os.path.getsize(path)
    return file_size,None