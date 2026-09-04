# CHECK: 待检查 - FastAPI 应用工厂 - 创建和配置 Web 应用实例

import logging

logger = logging.getLogger(__name__)

class App:
    """应用主容器类。

    持有所有服务实例，作为依赖注入的根节点。
    """
    def __init__(self, device_service, volume_service, super_device_service, super_volume_service, file_service):
        """初始化应用容器。

        Args:
            device_service: 设备服务实例。
            volume_service: 卷服务实例。
            super_device_service: 超级设备服务实例。
            super_volume_service: 超级卷服务实例。
            file_service: 文件服务实例。
        """
        self.device_service = device_service
        self.super_device_service = super_device_service
        self.volume_service = volume_service
        self.super_volume_service = super_volume_service
        # NOTE: file 子系统未完成（设计未定稿）：file_service 依赖为临时接入
        self.file_service = file_service
        logger.info("App initialized")
