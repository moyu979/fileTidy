from domain.storage.device.base import Device as DeviceBase
from domain.storage.volume.base import Volume
from infra.system.storage.volume.get_id import get_id
from infra.system.storage.volume.get_path import get_path


class volume_factory:
    def __init__(self) -> None:
        pass

    def new_volume(self,
        id: str|None,
        name: str,
        type: str,
        method: str,

        add_time,
        last_check_time,
        state: str|None,

        capacity: int|None,
        unique_mount_point: str|None,
        file_system: str|None,
        info: str|None,
        
        volume_path: str|None,
        based_on: list[DeviceBase]|None,
    ) -> Volume:
        # 路径与volume互验
        if volume_path is None:
            if id is None:
                raise ValueError("id and volume_path are both None")
            else:
                volume_path = get_path(id)
        elif volume_path is not None:
            if id is None:
                id = get_id(volume_path)
            else:
                if id != get_id(volume_path):
                    raise ValueError(f"the id of {volume_path} is not the same as the id given")
        # 校验按路径获得的信息与给定的是否一致
        if volume_path is not None:
            # 校验路径的类型是否与给定的类型一致
            # 这里现在有问题
            type_from_path = get_type(volume_path)
            if type==None or type==type_from_path:
                type=type_from_path
            else:
                raise ValueError(f"the type of {volume_path} is not the same as the type given, use auto get ")

        return Volume(
            id=id,
            name=name,
            type=type,
            method=method,
            add_time=add_time,
            last_check_time=last_check_time,
            state=state,
        )