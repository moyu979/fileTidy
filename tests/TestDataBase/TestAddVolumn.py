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
        

        volumeInfo2=DataBase_pb2.Volume()
        volumeInfo2.id="132456"
        volumeInfo2.volumeName="testVolume"
        volumeInfo2.capacity="100M"
        volumeInfo2.info="raid0"
        req=DataBase_pb2.AddVolumeRequest(volumeInfo=volumeInfo2)
        req.subid.append("132456")
        req.subid.append("123456")
        response=stub.AddVolume(req)
        result=response.result
        print(result,response.knownDiskInfo,response.info)

if __name__=="__main__":
    run()