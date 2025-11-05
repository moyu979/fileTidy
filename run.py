from core.init import init
from core.storage import storage_factory
from core.storage.tools import detect_device_type, get_storage

init()

print(storage_factory.StorageFactory.to_json())
# print(get_storage.get_storage())
# print(storage_factory.StorageFactory.register("/dev/sdb"))
# print(detect_device_type.is_disk_path("/dev/sda"))
# print(detect_device_type.is_tape_path("/dev/st0"))
# print(detect_device_type.get_device_type("/dev/sda"))
# print(detect_device_type.get_device_type("/dev/st0"))