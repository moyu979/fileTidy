import sys
import os
#sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.abspath("../grpc_protobuf"))
import threading
import grpc
import time
import logging

from concurrent import futures


from func.Controller.Server import ServerController as Server
from func.Controller.DataBase import _DataBaseController as Database

import Server_pb2_grpc as Server_pb2_grpc
import DataBase_pb2_grpc as DataBase_pb2_grpc



#from func import DataBase
from func import vars
#
import logging
def serve():
    
    vars.load_datas()
    current_thread = threading.current_thread()
    logging.debug(f"当前线程名: {current_thread.name}")
    logging.debug(f"当前线程ID: {current_thread.ident}")
    logging.debug(f"当前进程ID: {os.getpid()}")
    logging.debug(f"当前模块名: {__name__}")
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    #FileControl_pb2_grpc.add_FileControlServicer_to_server(FileControlServicer(), server)
    #DataBase_pb2_grpc.add_DataBaseServicer_to_server(DataBaseController.DataBaseServicer(), server)
    Server_pb2_grpc.add_ServerServicer_to_server(Server.ServerServicer(),server)
    DataBase_pb2_grpc.add_DataBaseServicer_to_server(Database.DataBaseServicer(),server)
    server.add_insecure_port(f'[::]:{vars.data["port"]}')
    server.start()
    try:
        while True:
            time.sleep(10000)
    except KeyboardInterrupt:
        server.stop(0)
        vars.save_datas()
        print(vars.data["serverid"])
 
if __name__ == '__main__':
  print("service start")
  
  serve()