import core.conf.conf as conf
import logging
platform=conf.get("platform")

if platform=="Darwin":
    from .Darwin import formatDisk as formatDisk
elif platform=="Windows":
    from .Windows import formatDisk as formatDisk
elif platform=="Linux":
    from .Linux import formatDisk as formatDisk
else:
    raise ValueError(f"platform {platform} unknown")

def get_physical_disks(disk,force=False):
    logging.error("这个功能要和volume联动，还没写完")
    """
        格式化disk指代的磁盘，force以强制
    """
    return formatDisk.format(disk,force)