# CHECK: AI生成 - 配置热更改造 - 更新 Config 调用方式

import argparse
import atexit
import logging

from application.app import App
from application.storage.device.service import DeviceService
from application.storage.file.file_service import file_service
from application.storage.super_device.service import SuperDeviceService
from application.storage.super_volume.factory import super_volume_factory
from application.storage.super_volume.service import super_volume_service
from application.storage.volume.service import VolumeService

from infra.config.app_config import AppConfig
from infra.log.logger import setup_logging
from infra.system.runtime import init_sys_infra
from infra.operation_log.operation_log import setup_event_logger
from infra.persistence.database import build_session_factory
from infra.persistence.init_db import init_database
from infra.persistence.storage.device_repository import DeviceRepository
from infra.persistence.storage.file_repository import file_repository
from infra.persistence.storage.super_device_repository import SuperDeviceRepository
from infra.persistence.storage.super_volume_repo import super_Volume_repository
from infra.persistence.storage.volume_repository import VolumeRepository
# volume 系统操作已改为直接函数调用，不再需要 adapter
from infra.common.hash import FileHasher

# TODO(P0): 整个项目没有任何测试，需要在重构前建立 pytest 测试框架作为安全网
logger = logging.getLogger(__name__)

def bootstrap(args: argparse.Namespace):
    """启动引导函数，初始化应用所需的所有组件。

    执行流程：
    1. 加载配置
    2. 配置日志系统
    3. 创建数据库会话工厂并初始化数据库
    4. 实例化所有仓储（Repository）和服务（Service）
    5. 组合成 App 对象

    Args:
        args: 命令行参数命名空间对象，包含 data_dir、modes 等属性。

    Returns:
        tuple[App, Config]: 返回 (应用实例, 配置对象) 的元组。
    """
    # data_dir 是数据根目录（如 ./datas），AppConfig 期望传入直接包含 yaml 的 settings 子目录
    config = AppConfig(args.data_dir / "settings", workspace_path=args.data_dir)
    # ConfigWatcher 在构造时自动启动（首个 SingleFileConfig 注册触发），无需手动启动
    atexit.register(config.stop_auto_reload)

    # system infra 初始化：注入配置以确定当前 OS，供 device 等平台分发使用
    init_sys_infra(config)

    setup_logging(config)
    setup_event_logger(config)
    logger.info("Bootstrap log completed")

    session_factory, engine = build_session_factory(config["database"]["path"])
    init_database(engine, session_factory)

    # # 设备 —— 仓库保持类实例，系统操作改为直接函数调用
    # device_repository_instance = DeviceRepository(session_factory)
    # device_service_instance = DeviceService(device_repository_instance)

    # super_device_repository_instance = SuperDeviceRepository(session_factory)
    # super_device_service_instance = SuperDeviceService(super_device_repository_instance, device_repository_instance)

    # file_repository_instance = file_repository(session_factory)
    # file_hasher = FileHasher(config["hash"])
    # file_service_instance = file_service(file_repository_instance, file_hasher)

    # volume_repository_instance = VolumeRepository(session_factory)
    # volume_service_instance = VolumeService(
    #     volume_repository_instance,
    #     file_service_instance,
    #     device_repository_instance,
    #     super_device_repository_instance,
    # )

    # super_volume_repository_instance = super_Volume_repository(session_factory)
    # super_volume_factory.set_volume_repository(volume_repository_instance)
    # super_volume_service_instance = super_volume_service(
    #     super_volume_repository_instance,
    #     volume_repository_instance,
    # )

    # app = App(
    #     device_service_instance,
    #     volume_service_instance,
    #     super_device_service_instance,
    #     super_volume_service_instance,
    #     file_service_instance,
    # )

    # logger.info("app bootstrap completed")
    # return app, config
    return None,None
