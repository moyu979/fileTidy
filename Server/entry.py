import sys
import os
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.abspath("../grpc_protobuf"))
import threading
import grpc
import time

from func import ServerController
import grpc_protobuf.Server_pb2_grpc as Server_pb2_grpc
from func import DataBase
import grpc_protobuf.DataBase_pb2_grpc as DataBase_pb2_grpc

from concurrent import futures

#from func import DataBase
from func import vars
#
#
def serve():
    vars.load_datas()
    print(vars.data["serverid"],222)

    current_thread = threading.current_thread()
    print(f"当前线程名: {current_thread.name}")
    print(f"当前线程ID: {current_thread.ident}")
    print(f"当前进程ID: {os.getpid()}")
    print(f"当前模块名: {__name__}")
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    #FileControl_pb2_grpc.add_FileControlServicer_to_server(FileControlServicer(), server)
    #DataBase_pb2_grpc.add_DataBaseServicer_to_server(DataBase.DataBaseServicer(), server)
    Server_pb2_grpc.add_ServerServicer_to_server(ServerController.ServerServicer(),server)
    DataBase_pb2_grpc.add_DataBaseServicer_to_server(DataBase.DataBaseServicer(),server)
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