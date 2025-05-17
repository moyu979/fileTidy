import logging


class Volume:
    def __init__(self):
        self.id = None
        self.name = None
        self.capacity = None

        self.add_time = None
        self.last_check = None
        self.healthy = None
        self.info = None

        self.need_all=None

        self.sub_volumes = []

        self.mount_point = None

    def set_volume_interactive(self):
        logging.error("set_volume_interactive not finished")
        
    def set_volume(self, info_dict,mount_point=None):
        """
        根据 info_dict 的键值对设置存储对象的属性。
        :param info_dict: 包含存储对象属性的字典。
        """
        # 定义允许设置的属性
        allowed_keys = {"id", "name", "capacity", "add_time", "last_check", "healthy", "info", "need_all"}
        
        for key, value in info_dict.items():
            if key in allowed_keys:
                setattr(self, key, value)

    def set_sub_volume(self, sub_volume):
        """
        设置子卷。
        :param sub_volume: 子卷对象。
        """
        self.sub_volumes=sub_volume

    def to_database(self):
        """
        将卷信息存储到数据库中。
        """
        # 这里需要实现将卷信息存储到数据库的逻辑
        logging.error("to_database not finished")

    def check_volume(self):
        """
        检查卷的健康状态（全量扫描）。
        """
        # 这里需要实现检查卷健康状态的逻辑
        logging.error("check_volume not finished")

    def monitor_volume(self):
        """
        监控卷的健康状态（增量扫描）。
        """
        # 这里需要实现监控卷健康状态的逻辑
        logging.error("monitor_volume not finished")

    def formate_volume(self):
        # 格式化磁盘
        logging.error("formate_volume not finished")

    def get_volume_usage(self):
        """
        获取卷的使用情况。
        :return: 卷的使用情况。
        """
        # 这里需要实现获取卷使用情况的逻辑
        logging.error("get_volume_usage not finished")