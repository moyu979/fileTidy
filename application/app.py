import logging

logger = logging.getLogger(__name__)

class App:
    def __init__(self,device_service):
        self.device_service = device_service
        logger.info("App initialized")
