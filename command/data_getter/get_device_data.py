import logging

import core.component.add_device_data as add_device_data
import core.tools.confs as confs
import core.tools.generater as generater
class get_device_data:
    def __init__(self,device_kind=None):
        self.phy_storage:add_device_data.device_data=add_device_data.device_data()
        self.kind=device_kind
        self.phy_storage.kind=device_kind
    def __call__(self):
        self.get_kind()
        self.get_id()
        self.get_add_time()
        self.get_last_check()
        self.get_disk_name()
        self.get_health()
        self.get_capacity()
        self.get_info()
        return self.phy_storage

    def get_kind(self):
        if self.phy_storage.kind=="tape":
            print("please input your tape kind:")
            for k,v in confs.device_kind.items():
                if k.startswith("2"):
                    print(f"\t{k}:{v}")
        
        elif self.phy_storage.kind=="disk":
            print("please input your disk kind:")
            for k,v in confs.device_kind.items():
                if k.startswith("0") or k.startswith("1"):
                    print(f"\t{k}:{v}")
        elif self.phy_storage.kind=="usb":
            print("please input your usb device kind:")
            for k,v in confs.device_kind.items():
                if k.startswith("0") or k.startswith("3"):
                    print(f"\t{k}:{v}")

        self.phy_storage.kind=input()

        if self.phy_storage.kind in confs.device_kind.keys():
            self.phy_storage.kind=confs.device_kind[self.phy_storage.kind]
        if self.phy_storage.kind not in confs.device_kind.values():
            err=f"kind kind {self.phy_storage.kind} not in known kind, retry"
            logging.error(err)
            return self.get_kind()

    def get_id(self):
        if self.kind=="tape":
            self.phy_storage.id=input("please input tape id, it will be auto generated if keep empty:")
            if self.phy_storage.id=="":
                self.phy_storage.id=generater.get_a_device_id()
        else:
            self.phy_storage.id=input("please input device id:")
            if id=="":
                err=f"try to give an empty id to a device suppose to have a fix id, retry"
                logging.error(err)
                self.get_id()

    def get_add_time(self):
        self.phy_storage.add_time=input("please input add time, it will be auto generated if keep empty:")
        if self.phy_storage.add_time=="":
            self.phy_storage.add_time=generater.fileTimeSecond()

    def get_last_check(self):
        self.phy_storage.last_check=input("please input check time, it will be auto generated as never if keep empty:")
        if self.phy_storage.last_check=="":
            self.phy_storage.last_check="0000:00:00 00:00"

    def get_disk_name(self):
        self.phy_storage.disk_name=input("please input disk name, it will be NULL if keep empty:")
        if self.phy_storage.disk_name=="":
            self.phy_storage.disk_name==None

    def get_health(self):
        print("please input disk healthy, default value is \"health\":")
        for k,v in confs.device_health.items():
            print(f"\t{k},{v}")
        self.phy_storage.health=input()
        if self.phy_storage.health=="":
            self.phy_storage.health="1"
        if self.phy_storage.health in confs.device_health.keys():
            self.phy_storage.health=confs.device_health[self.phy_storage.health]
        if self.phy_storage.health not in confs.device_health.values():
            err=f"unknown health state {self.phy_storage.health},retry"
            logging.error(err)
            self.get_health()
    
    def get_capacity(self):
        if self.phy_storage.kind in confs.capacity.keys():
            print(f"we can infer that your device has a capacity {confs.capacity[self.phy_storage.kind]} if kind is {self.phy_storage.kind}")
            print("do you want to change?(keep empty if you DO NOT want change)")
            self.phy_storage.capacity=input()
            if self.phy_storage.capacity=="":
                self.phy_storage.capacity=confs.capacity[self.phy_storage.kind]
        else:
            self.phy_storage.capacity=input("please tell us the capacity of device, not necessery")
            if self.phy_storage.capacity=="":
                self.phy_storage.capacity="unknow"

    def get_info(self):
        self.phy_storage.info=input("does anything need to add?")