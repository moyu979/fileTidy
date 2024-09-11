import sys
sys.path.append("..")
import grpc
import time
import grpc_protobuf.FileControl_pb2 as FileControl_pb2
import grpc_protobuf.FileControl_pb2_grpc as FileControl_pb2_grpc
import grpc_protobuf.DataBase_pb2 as DataBase_pb2
import grpc_protobuf.DataBase_pb2_grpc as DataBase_pb2_grpc

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = DataBase_pb2_grpc.DataBaseStub(channel)
        response=stub.InitDataBase(DataBase_pb2.InitRequest())
        print("Client received: ",response.result,response.info)
 
 
if __name__ == '__main__':
  run()