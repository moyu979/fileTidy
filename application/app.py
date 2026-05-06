import logging

logger = logging.getLogger(__name__)

class App:
    def __init__(self,device_service, volume_service):
        self.device_service = device_service
        
        self.volume_service = volume_service
        logger.info("App initialized")
