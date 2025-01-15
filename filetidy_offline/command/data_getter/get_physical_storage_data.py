import logging

import core.component.physical_storage as physical_storage
import core.tools.confs as confs
def get_physical_storage_data(disk_kind=None):
    phy_storage=physical_storage.physical_storage()
    if disk_kind:
        if disk_kind=="tape":
            print("please input your device kind")
            for k,v in confs.disk_kind.items():
                if k.startswith("1"):
                    print(f"\t{k}:{v}")
            phy_storage.kind=input()
            if phy_storage.kind in confs.disk_kind.keys():
                phy_storage.kind=confs.disk_kind[phy_storage.kind]
            if phy_storage.kind not in confs.tape:
                err=f"tape kind {phy_storage.kind} not in known tape kind"
                logging.error(err)
                return None,err
        if disk_kind=="disk":
            print("please input your device kind")
            for k,v in confs.disk_kind.items():
                if k.startswith("0"):
                    print(f"\t{k}:{v}")
            phy_storage.kind=input()
            if phy_storage.kind in confs.disk_kind.keys():
                phy_storage.kind=confs.disk_kind[phy_storage.kind]
            if phy_storage.kind not in confs.disk:
                err=f"disk kind {phy_storage.kind} not in known disk kind"
                logging.error(err)
                return None,err
        else:
            err=f"disk kind {disk_kind} not in known device kind"
            logging.error(err)
            return None,err
    else:
        print("please input your device kind")
        for k,v in confs.disk_kind.items():
            print(f"\t{k}:{v}")
        phy_storage.kind=input()
        if phy_storage.kind in confs.disk_kind.keys():
            phy_storage.kind=confs.disk_kind[phy_storage.kind]

        if phy_storage.kind not in confs.disk_kind.values():
            err=f"disk kind {phy_storage.kind} not in known disk kind"
            logging.error(err)
            return None,err

    if phy_storage.kind in confs.tape:
        phy_storage.id=input("please input tape id, it will be auto generated if keep empty:")
    else:
        phy_storage.id=input("please input disk id:")
        if id=="":
            err=f"try to give an empty id to disk"
            logging.error(err)
            return None,err

    phy_storage.add_time=input("please input add time, it will be auto generated if keep empty:")
    phy_storage.last_check=input("please input add time, it will be auto generated if keep empty:")
    phy_storage.disk_name=input("please input disk name, could be empty:")
    
    print("please input disk healthy")
    print("default:health")
    for k,v in confs.health.items():
        print(f"\t{k},{v}")
    phy_storage.health=input()
    if phy_storage.health in confs.health.keys():
        phy_storage.health=confs.health[phy_storage.health]
    if phy_storage.health not in confs.health.values():
        err=f"unknown health state {phy_storage.health}"
        logging.error(err)
        return None,err
    
    if phy_storage.kind in confs.capacity.keys():
        print(f"we can infer that your device has a capacity {confs.capacity[phy_storage.kind]} if kind is {phy_storage.kind}")
        print("do you want to change?(keep empty if you want default)")
        phy_storage.capacity=input()
        if phy_storage.capacity=="":
            phy_storage.capacity=confs.capacity[phy_storage.kind]
    else:
        phy_storage.capacity=input("please tell us the capacity of device, could be empty")

    phy_storage.info=input("does anything need to add?")
    return phy_storage,None
