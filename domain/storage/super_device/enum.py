import enum
class SuperDeviceState(enum.Enum):
    HEALTHY = "healthy" # 正常使用的
    DANGER = "danger" # 危险，冗余出现故障，但是暂时可以使用，主要用来描述有坏到等隐患的设备
    DEGRADING = "degrading"
    FAULT = "fault" # 故障，无法使用
    REMOVED = "removed" # 已移除（软删除，记录仍保留在数据库中）