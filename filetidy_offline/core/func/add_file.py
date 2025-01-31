import core.component.add_file_data as add_file_data

def add_file(add_file_data:add_file_data.file_data):
    _,err=add_file_data.check()
    _,err=add_file_data.execute()