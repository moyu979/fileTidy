import sys
sys.path.append("..")
import grpc
import time
import grpc_protobuf.FileControl_pb2 as FileControl_pb2
import grpc_protobuf.FileControl_pb2_grpc as FileControl_pb2_grpc

import grpc_protobuf.DataBase_pb2 as DataBase_pb2
import grpc_protobuf.DataBase_pb2_grpc as DataBase_pb2_grpc
from concurrent import futures

from func import DataBase
from func import vars


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    #FileControl_pb2_grpc.add_FileControlServicer_to_server(FileControlServicer(), server)
    DataBase_pb2_grpc.add_DataBaseServicer_to_server(DataBase.DataBaseServicer(), server)
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