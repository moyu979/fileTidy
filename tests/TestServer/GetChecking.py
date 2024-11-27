import sys
import os
sys.path.append(os.path.abspath("../.."))
sys.path.append(os.path.abspath("../../grpc_protobuf"))
import grpc_protobuf.Server_pb2 as Server_pb2
import grpc_protobuf.Server_pb2_grpc as Server_pb2_grpc
import grpc
def run(id=None):
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = Server_pb2_grpc.ServerStub(channel)
        request=Server_pb2.idMessage()
        if id:
            request.checkId=id
        response=stub.GetChecking(request)
        print("result:",response.result)
        for id,info in zip(response.checkId,response.checkInfo):
            print(id,info)

if __name__=="__main__":
    print("run()")
    run()
    print("run(1)")
    run("1")
    print("run(3)")
    run("3")