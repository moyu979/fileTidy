import core.conf.conf as conf

platform = conf.get("platform")

if platform == "Darwin":
    from .Darwin import is_partition as _is_partition
elif platform == "Windows":
    from .Windows import is_partition as _is_partition
elif platform == "Linux":
    from .Linux import is_partition as _is_partition
else:
    raise ValueError(f"platform {platform} unknown")


def is_partition(path):
    return _is_partition.is_partition(path)
