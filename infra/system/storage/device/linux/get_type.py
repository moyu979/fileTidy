# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# CHECK: AI生成 - linux 平台：获取设备类型
"""linux —— 获取设备类型。"""

from ._common import _disk_info


def get_type(path: str) -> str:
    """获取设备类型。

    根据 ROTA（是否旋转）和型号判断设备类型。

    Args:
        path: 设备路径。

    Returns:
        设备类型字符串："ssd", "hdd", "tf_sd_card"。
    """
    info = _disk_info(path)
    rota = info.get("rota")
    model = (info.get("model") or "").lower()
    if "sd" in model or "flash" in model:
        return "tf_sd_card"
    if rota == 0:   # 非旋转 → SSD
        return "ssd"
    return "hdd"
