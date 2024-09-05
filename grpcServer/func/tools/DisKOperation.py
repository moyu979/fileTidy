import os
def get_Size(path,type)->str:
    size="0B"
    if type=="SSD" or type=="HDD":
        res=os.popen(f"lsblk | grep {path}").read()
        # todo : analysis result and get open
    elif type=="tape":
        res=os.popen(f"mt -f /dev/{path}").read()
        # todo : analysis result and get open
    return size
