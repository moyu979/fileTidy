import core.component.add_device_data as add_device_data

def add_disk(disk:add_device_data.device_data):
    _,err=disk.check()
    if err:
        return None,err
    
    _,err=disk.add_to_db()
    if err:
        return None,err
    
    return None,None