import grpc_protobuf.Server_pb2 as Server_pb2
import grpc_protobuf.Server_pb2_grpc as Server_pb2_grpc
import os
import sqlite3
from func import vars
from func.tools import _fileTime
from grpcServer.func.tools.DisKOperation import *
class ServerServicer(Server_pb2_grpc.DataBase):
    def TestAccess(self,request,context):
        print(f"received request with info {request.retuestInfo}")
        return Server_pb2.TestAccessAnswer(answerInfo="result")

    def GetChecking(self,request,context):
        if request.checkId!=None:
            pass