import subprocess
import re
import os


def get_physical_disks():
    """
    return{
        "name": name,
        "device": dev_path,
        "size": int(size),
        "serial": serial,
        "type": disk_type
    }
    """
    disks = []

    try:
        # 获取物理磁盘列表（不含分区等）
        output = subprocess.check_output(
            "lsblk -dn -o NAME,SIZE,TYPE --bytes", shell=True, encoding="utf-8"
        )
        lines = output.strip().splitlines()

        for line in lines:
            name, size, dev_type = line.strip().split()
            if dev_type != "disk":
                continue  # 跳过非物理磁盘

            dev_path = f"/dev/{name}"
            rotational_path = f"/sys/block/{name}/queue/rotational"

            # 判断是否为SSD
            try:
                with open(rotational_path, "r") as f:
                    rotational = f.read().strip()
                disk_type = "SSD" if rotational == "0" else "HDD"
            except Exception:
                disk_type = "Unknown"

            # 获取序列号
            try:
                udevadm_out = subprocess.check_output(
                    f"udevadm info --query=all --name={dev_path}",
                    shell=True,
                    encoding="utf-8",
                    stderr=subprocess.DEVNULL,
                )
                serial_match = re.search(
                    r"ID_SERIAL_SHORT=(.+)", udevadm_out
                ) or re.search(r"ID_SERIAL=(.+)", udevadm_out)
                serial = serial_match.group(1).strip() if serial_match else "N/A"
            except Exception:
                serial = "N/A"

            disks.append(
                {
                    "name": name,
                    "device": dev_path,
                    "size": int(size),
                    "id": serial,
                    "type": disk_type,
                }
            )

    except subprocess.CalledProcessError as e:
        print("Error collecting disk info:", e)

    return disks


if __name__ == "__main__":
    for d in get_physical_disks():
        print(f"name: {d['name']}")
        print(f"Device: {d['device']}")
        print(f"  Size: {d['size']}")
        print(f"  Type: {d['type']}")
        print(f"  Serial: {d['id']}\n")
