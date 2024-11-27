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
        diskInfo=DataBase_pb2.Disk()
        diskInfo.id="1234567"
        diskInfo.diskName="testDisk"
        diskInfo.capacity="100M"
        diskInfo.kind="HDD"
        response=stub.AddDisk(DataBase_pb2.AddDiskRequest(diskInfo=diskInfo,forceDo=False))
        result=response.result
        print(result,response.knownDiskInfo,response.info)

        diskInfo=DataBase_pb2.Disk()
        diskInfo.id="1234567"
        diskInfo.diskName="testDisk"
        diskInfo.capacity="100M"
        diskInfo.kind="HDD"
        response=stub.AddDisk(DataBase_pb2.AddDiskRequest(diskInfo=diskInfo,forceDo=False))
        result=response.result
        print(result,response.knownDiskInfo,response.info)

        # diskInfo=DataBase_pb2.Disk()
        # diskInfo.diskName="testDisk"
        # diskInfo.capacity="100M"
        # diskInfo.kind="HDD"
        # response=stub.AddDisk(DataBase_pb2.AddDiskRequest(diskPath="PHYSICALDRIVE0",diskInfo=diskInfo,forceDo=False))
        # result=response.result
        # print(result,response.knownDiskInfo,response.info)

if __name__=="__main__":
    run()