import sys
import os
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.abspath("../.."))
sys.path.append(os.path.abspath("../../grpc_protobuf"))
#import publicImport
import grpc_protobuf.DataBase_pb2 as DataBase_pb2
import grpc_protobuf.DataBase_pb2_grpc as DataBase_pb2_grpc
import grpc

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = DataBase_pb2_grpc.DataBaseStub(channel)
        response=stub.GetDisk(DataBase_pb2.GetDiskRequest(id="id",info="0"))
        result=response.result
        data=response.diskinfo
        print(result)
        for i in data:
            print(i.id,i.addTime)

if __name__=="__main__":
    run()