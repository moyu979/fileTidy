#todo 检查正确性
import core.component.add_volume_data as add_volume_data
def add_volume(volume:add_volume_data):
    _,err=volume.check()
    if err:
        return None,err
    
    _,err=volume.execute()
    if err:
        return None,err
    
    return None,None