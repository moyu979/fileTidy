from core.component.check_file_data import check_file

import logging
def check_file(check_file_data:check_file):
    check_file_data.check()

    if check_file_data.execute():
        logging.warning("has error")
    else:
        logging.info("success")

    
