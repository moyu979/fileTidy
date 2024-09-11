import sys
import os
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.abspath("../grpc_protobuf"))
import grpc
import time
#import grpc_protobuf.FileControl_pb2 as FileControl_pb2
#import grpc_protobuf.FileControl_pb2_grpc as FileControl_pb2_grpc

#import grpc_protobuf.DataBase_pb2 as DataBase_pb2
#import grpc_protobuf.DataBase_pb2_grpc as DataBase_pb2_grpc

import grpc_protobuf.Server_pb2 as Server_pb2
import grpc_protobuf.Server_pb2_grpc as Server_pb2_grpc

from concurrent import futures

#from func import DataBase
#from func import vars
from func import ServerController

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    #FileControl_pb2_grpc.add_FileControlServicer_to_server(FileControlServicer(), server)
    #DataBase_pb2_grpc.add_DataBaseServicer_to_server(DataBase.DataBaseServicer(), server)
    Server_pb2_grpc.add_ServerServicer_to_server(ServerController.ServerServicer(),server)

    server.add_insecure_port('[::]:50051')
    server.start()
    try:
        while True:
            time.sleep(10000)
    except KeyboardInterrupt:
        server.stop(0)
 
if __name__ == '__main__':
  print("service start")
  
  serve()