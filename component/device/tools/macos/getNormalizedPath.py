def get_normalized_path(dev_path):
    if dev_path.startswith('/dev/disk'):
        return dev_path
    elif dev_path.startswith('disk'):
        return f'/dev/{dev_path}'
    else:
        return None