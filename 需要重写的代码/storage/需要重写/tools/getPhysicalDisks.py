import core.conf.conf as conf

platform = conf.get("platform")

if platform == "Darwin":
    from .Darwin import getPhysicalDisks as getPhysicalDisks
elif platform == "Windows":
    from .Windows import getPhysicalDisks as getPhysicalDisks
elif platform == "Linux":
    from .Linux import getPhysicalDisks as getPhysicalDisks
else:
    raise ValueError(f"platform {platform} unknown")


def get_physical_disks():
    return getPhysicalDisks.get_physical_disks()
