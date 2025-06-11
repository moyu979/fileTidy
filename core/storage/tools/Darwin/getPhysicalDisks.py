import subprocess
import re
import os
import logging
def get_physical_disks():
    logging.error("mac 版本下的get_physical_disks功能还未实现")


if __name__ == "__main__":
    for d in get_physical_disks():
        print(f"Device: {d['device']}")
        print(f"  Size: {d['size']}")
        print(f"  Type: {d['type']}")
        print(f"  Serial: {d['serial']}\n")
