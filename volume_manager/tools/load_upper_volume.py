import volume_manager.volumeFactory as volumeFactory
from pathlib import Path
import os
def load_root_volume_id(path=None):
    """
    Load the root volume from the database.
    :param path: The path to the volume.
    :return: The root Volume instance.
    """
    if path is None:
        volume = volumeFactory.VolumeFactory.load_volume_from_database(id=0)
        return volume
    else:
        upper=Path(path).parent
        while upper!=path:
            path=upper
            maybe=os.path.join(upper,"volume_id")
            if os.path.exists(maybe):
                files=os.listdir(maybe)
                id=files[0]
                return volumeFactory.VolumeFactory.load_volume_from_database(id=id),upper
        return volumeFactory.VolumeFactory.load_volume_from_database(id=0),"/"
