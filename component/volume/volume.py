class Volume:
    def __init__(self, orm_model=None,volume_path=None):
        if orm_model is not None:
            self.orm_model = orm_model
            if volume_path is not None:
                self.volume_path = volume_path
        else:
            self.orm_model = None
            if volume_path is not None:
                self.volume_path = volume_path
            else:
                raise ValueError("volume_path 和 orm_model 不能同时为空")