import logging
import os

import file_manager.tools.Hash as Hash
class Files:
    @classmethod
    def insert_files(self,file_path):
        # Logic to insert files into the system
        for root,dirs,files in os.walk(self.file_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_hash = Hash.getAHash(file_path)

                # Assuming we have a function to insert the file into the database
                self.insert_file(file_path)
        logging.error(f"Inserting files from {self.file_path} not finished")
    @classmethod
    def move_files(self):
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