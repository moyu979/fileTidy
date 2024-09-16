import sys
import os
sys.path.append(os.path.abspath("../.."))
sys.path.append(os.path.abspath("../../grpc_protobuf"))
import publicImport
import grpc_protobuf.Server_pb2 as Server_pb2
import grpc_protobuf.Server_pb2_grpc as Server_pb2_grpc
import grpc
def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = Server_pb2_grpc.ServerStub(channel)
        response=stub.TestAccess(Server_pb2.TestAccessRequest(requestInfo="test Access"))
        print("Client received: ",response.answerInfo)

if __name__=="__main__":
    run()