import logging

logger = logging.getLogger(__name__)

def tape_check(path):
    logger.info("数据磁带的检查请直接使用volume级的数据完整性校验")
    return "ok"