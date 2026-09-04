# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: ai生成，待检查 - 领域层 Device 枚举定义 - 设备类型/状态常量

from __future__ import annotations

import enum

from domain.common.menu import _Menu, _MenuOption


class DeviceState(enum.Enum):
    """设备状态枚举。

    定义设备可能处于的各种健康状态。
    """
    UNKNOWN = "unknown" # 刚接入，尚未检测健康状态
    HEALTHY = "healthy" # 正常使用的
    DANGER = "danger" # 危险，但是暂时可以使用，主要用来描述有坏道等隐患的设备
    FAULT = "fault" # 故障，无法使用
    REMOVED = "removed" # 已移除（软删除，记录仍保留在数据库中）


class LtoGeneration(enum.Enum):
    """磁带 LTO 代次枚举（LTO-1 至 LTO-9）。

    该值存储于设备 info（JSON）的 "generation" 键中。
    """
    LTO1 = "lto1"
    LTO2 = "lto2"
    LTO3 = "lto3"
    LTO4 = "lto4"
    LTO5 = "lto5"
    LTO6 = "lto6"
    LTO7 = "lto7"
    LTO8 = "lto8"
    LTO9 = "lto9"


class DeviceInterface(enum.Enum):
    """磁盘接口枚举。

    该值存储于设备 info（JSON）的 "interface" 键中。
    """
    SATA = "sata"
    SAS = "sas"
    NVME = "nvme"
    NGFF = "ngff"    # M.2 SATA（旧称 NGFF）
    MSATA = "msata"
    U2 = "u2"
    USB = "usb"


class DeviceFormFactor(enum.Enum):
    """磁盘物理尺寸/形态枚举。

    说明：2.5/3.5 为英寸；M.2 系列为毫米长度（如 2280 = 22×80mm）。
    该值存储于设备 info（JSON）的 "form_factor" 键中。
    """
    TWO_POINT_FIVE = "2.5"
    THREE_POINT_FIVE = "3.5"
    M2_2230 = "2230"
    M2_2260 = "2260"
    M2_2280 = "2280"
    M2_22110 = "22110"


class DeviceStateMenu(_Menu):
    """设备状态菜单。"""
    title = "设备状态"
    value_type = DeviceState
    default = DeviceState.UNKNOWN
    options = [
        _MenuOption("1", DeviceState.UNKNOWN,  "UNKNOWN", "未知（默认）"),
        _MenuOption("2", DeviceState.HEALTHY,  "HEALTHY", "健康"),
        _MenuOption("3", DeviceState.DANGER,   "DANGER",  "危险"),
        _MenuOption("4", DeviceState.FAULT,    "FAULT",   "故障"),
        _MenuOption("5", DeviceState.REMOVED,  "REMOVED", "已移除"),
    ]


class DeviceTypeMenu(_Menu):
    """设备类型菜单。

    磁带为普通选项（"4" → "tape"）；LTO 代次由 LtoGenerationMenu 单独录入，
    不再支持旧式 "45" 带代次编码（全新重构，无历史包袱）。
    """
    title = "设备类型"
    # value_type=None → from_code 直接返回类型字符串
    options = [
        _MenuOption("1", "ssd",        "SSD",    "固态硬盘"),
        _MenuOption("2", "hdd",        "HDD",    "机械硬盘"),
        _MenuOption("3", "tf_sd_card", "TF 卡",  "tf_sd_card"),
        _MenuOption("4", "tape",       "磁带",   "LTO 代次由 LtoGenerationMenu 录入"),
    ]


class LtoGenerationMenu(_Menu):
    """LTO 代次菜单。"""
    title = "LTO 代次"
    value_type = LtoGeneration
    options = [
        _MenuOption("1", "lto1", "LTO-1", ""),
        _MenuOption("2", "lto2", "LTO-2", ""),
        _MenuOption("3", "lto3", "LTO-3", ""),
        _MenuOption("4", "lto4", "LTO-4", ""),
        _MenuOption("5", "lto5", "LTO-5", ""),
        _MenuOption("6", "lto6", "LTO-6", ""),
        _MenuOption("7", "lto7", "LTO-7", ""),
        _MenuOption("8", "lto8", "LTO-8", ""),
        _MenuOption("9", "lto9", "LTO-9", ""),
    ]


class InterfaceMenu(_Menu):
    """磁盘接口菜单。"""
    title = "磁盘接口"
    value_type = DeviceInterface
    options = [
        _MenuOption("1", "sata",  "SATA",  "串行 ATA"),
        _MenuOption("2", "sas",   "SAS",   "串行 SCSI"),
        _MenuOption("3", "nvme",  "NVMe",  "M.2/PCIe NVMe"),
        _MenuOption("4", "ngff",  "NGFF",  "M.2 SATA（旧称 NGFF）"),
        _MenuOption("5", "msata", "mSATA", "mini-SATA"),
        _MenuOption("6", "u2",    "U.2",   "2.5 寸 NVMe"),
        _MenuOption("7", "usb",   "USB",   "USB 外置"),
    ]


class FormFactorMenu(_Menu):
    """磁盘物理尺寸菜单。"""
    title = "物理尺寸"
    value_type = DeviceFormFactor
    options = [
        _MenuOption("1", "2.5",    "2.5 英寸",   ""),
        _MenuOption("2", "3.5",    "3.5 英寸",   ""),
        _MenuOption("3", "2230",   "M.2 2230",   "22×30mm"),
        _MenuOption("4", "2260",   "M.2 2260",   "22×60mm"),
        _MenuOption("5", "2280",   "M.2 2280",   "22×80mm"),
        _MenuOption("6", "22110",  "M.2 22110",  "22×110mm"),
    ]