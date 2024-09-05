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
def add_physical_storage(name,kind="disk"):
    if kind=="disk":
        #如果是硬盘的话，存在无根情况，此时使用disk的唯一id标记其信息
        answer=os.popen(f"lsblk | grep {name}")
        lines=answer.read().split("\n")
        if len(lines)==1:
            return 1,"not such disk"
        elif len(lines)>2:
            return 2,"more than one disk has that name"

        datas=[x for x in lines[0].split(' ') if x]
        NAME=datas[0]
        SIZE=datas[3]
        MOUNTPOINTS=None
        if len(datas)>=7:
            MOUNTPOINTS=datas[6]
            #询问是否将标记加入

        
        
    elif kind in vars.tape:
        #如果是磁带的话，磁带不存在唯一的识别标志，因此需要特殊操作
        pass
