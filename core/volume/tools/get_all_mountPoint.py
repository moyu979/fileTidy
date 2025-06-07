import core.conf.conf as conf

platform=conf.get("platform")

if platform=="Darwin":
    from .Darwin import get_all_mountPoint as _get_all_mount_point
elif platform=="Windows":
    from .Windows import get_all_mountPoint as _get_all_mount_point
elif platform=="Linux":
    from .Linux import get_all_mountPoint as _get_all_mount_point
else:
    raise ValueError(f"platform {platform} unknown")

def get_all_mount_point():
    return _get_all_mount_point.get_all_mount_points()