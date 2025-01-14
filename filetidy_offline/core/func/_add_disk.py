import core.component.physical_storage as physical_storage

def add_disk(disk:physical_storage.physical_storage):
    _,err=disk.check()
    if err:
        return None,err
    
    _,err=disk.add_to_db()
    if err:
        return None,err
    
    return None,None