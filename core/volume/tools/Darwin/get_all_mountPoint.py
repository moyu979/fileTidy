import subprocess

def get_all_partitions():
    output = subprocess.check_output(['diskutil', 'list'], text=True)
    partitions = []
    current_disk = None
    #print(output)
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("/dev/disk"):
            current_disk = line.split()[0]
        elif current_disk and line and line[0].isdigit():
            parts = line.split()
            if len(parts) >= 5:
                partition = {
                    "disk": current_disk,
                    "index": parts[0].rstrip(':'),
                    "type": parts[1],
                    "name": parts[2],
                    "size": parts[-3].replace("*","")+" "+parts[-2],
                    "identifier": parts[-1]
                }
                partitions.append(partition)
    return partitions

def get_mount_point(identifier):
    try:
        output = subprocess.check_output(['diskutil', 'info', identifier], text=True)
        #print(output)
        for line in output.splitlines():
            if 'Mount Point:' in line:
                # 格式一般是 "   Mount Point: /Volumes/YourVolume"
                mount_point = line.split(':', 1)[1].strip()
                return mount_point if mount_point != 'Not Mounted' else ''
    except subprocess.CalledProcessError:
        return ''
    return ''

def get_all_mount_points():
    all_has_part=[]
    partitions = get_all_partitions()
    for p in partitions:
        mount_point = get_mount_point(p['identifier'])
        if len(mount_point)!=0 and p['name']=='Volume':
            all_has_part.append([p['identifier'],p['name'],p['size'],mount_point])
            #print(f"{p['identifier']:10} | {p['name']:20} | Mount Point: {mount_point}")
    return all_has_part