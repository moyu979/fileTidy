# CHECK: 待检查 - 共享工具 - 时间默认值工具

"""跨层约定的时间字段默认值（设备巡检等）。"""

from datetime import datetime

# 表示「尚未产生真实巡检时间」的占位（Unix 纪元，naive UTC，与项目里 datetime.utcnow 风格一致）
LAST_CHECK_TIME_ORIGIN = datetime(1970, 1, 1, 0, 0, 0)
