"""
平台自动检测与分发。
"""

import sys

if sys.platform == "darwin":
    from .darwin import (
        get_capacity,
        get_healthy,
        get_path,
        get_serial,
        get_type,
        is_disk,
    )
elif sys.platform == "linux":
    from .linux import (
        get_capacity,
        get_healthy,
        get_path,
        get_serial,
        get_type,
        is_disk,
    )
elif sys.platform == "win32":
    from .win32 import (
        get_capacity,
        get_healthy,
        get_path,
        get_serial,
        get_type,
        is_disk,
    )
else:
    raise ImportError(f"不支持的平台: {sys.platform}")
