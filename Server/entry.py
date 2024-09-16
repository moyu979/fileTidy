import sys
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.abspath("../grpc_protobuf"))
import os
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
 
if __name__ == '__main__':
  
  print("service start")
  
  serve()