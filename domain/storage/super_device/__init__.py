# TODO: [AI生成-未检测] 本文件由 AI 生成，尚未经人工检测与审查。
# eager-import 变体：保证包被导入即注册表就绪
# （SuperDevice._registry 由 __init_subclass__ 自注册填充，变体必须被 import）
from domain.storage.super_device.variants.raidz import RaidzSuperDevice
from domain.storage.super_device.variants.single_super_device import SingleSuperDevice

__all__ = ["RaidzSuperDevice", "SingleSuperDevice"]
