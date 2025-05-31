import logging
import os
import volume_manager.temp.volumeFactory as VolumeFactory
import volume_manager.temp.volume as Volume
import file_manager.tools.Hash as Hash
import file_manager.file as File
from datetime import datetime

class Files:
    @classmethod
    def insert_files(self,file_path):
        logging.info(f"Inserting files from {file_path} to the system")
        # Logic to insert files into the system
        volume:Volume.Volume=VolumeFactory.VolumeFactory.load_volume_from_database(mount_point=file_path)

        for root,dirs,files in os.walk(file_path):
            for file in files:
                path=os.path.join(root,file)
                file=File.file()
                file.set_volume(volume.id)
                file.set_abspath(path=path)
                file.append_file()
        # logging.error(f"Inserting files from {file_path} not finished")
    @classmethod
    def move_files(self,from_dir,to_dir):
        # Logic to move files
        logging.error(f"Moving files not finished")
    @classmethod
    def delete_files(self):
        # Logic to delete files
        logging.error(f"Deleting files not finished")
    @classmethod
    def check_files(self):
        # Logic to check files
        logging.error(f"Checking files not finished")