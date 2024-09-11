import os
from .. import vars
def getMatchedDisk(diskName,SerialNumber):
    if vars.data["platform"]=="Windows":
        import wmi
        c=wmi.WMI()
        for physical_disk in c.Win32_DiskDrive():
            id:str=physical_disk.DeviceID
            get_name=id
            if get_name==diskName and physical_disk.SerialNumber==SerialNumber:
                return physical_disk.Size
        return None
    
def getDiskByPath(disk_path):
    if vars.data["platform"]=="Windows":
        import wmi
        c=wmi.WMI()
        for physical_disk in c.Win32_DiskDrive():
            id:str=physical_disk.DeviceID
            get_name=id.replace("\\","").replace(".","")
            if get_name==disk_path:
                return physical_disk.SerialNumber,physical_disk.Size
        return None,0
    
def getDiskBySerialNumber(disk_id):
    if vars.data["platform"]=="Windows":
        import wmi
        c=wmi.WMI()
        for physical_disk in c.Win32_DiskDrive():
            if physical_disk.SerialNumber==disk_id:
                return physical_disk.Size
        return None


class disk:
    def __init__(self) -> None:
        self.capacity=0
        self.SerialNumber=None
        
    def initByName(self,name):
        if vars.data["platform"]=="Windows":
            self.init_Name_windows(name)
        else:
            print("unknown platform")
            
    def initBySerialNumber(self,SerialNumber):
        if vars.data["platform"]=="Windows":
            return self.init_SerialNumber_windows(SerialNumber)
        else:
            print("unknown platform")
            return -1
        
    def init_Name_windows(self,name):
        import wmi
        c=wmi.WMI()
        for physical_disk in c.Win32_DiskDrive():
            id:str=physical_disk.DeviceID
            get_name=id.replace("\\","").replace(".","")
            if get_name==name:
                self.SerialNumber=physical_disk.SerialNumber
                self.capacity=physical_disk.Size

    def init_SerialNumber_windows(self,SerialNumber):
        self.SerialNumber=physical_disk.SerialNumber
        import wmi
        c=wmi.WMI()
        for physical_disk in c.Win32_DiskDrive():
            id:str=physical_disk.SerialNumber
            if id==SerialNumber:
                self.capacity=physical_disk.Size
        

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
