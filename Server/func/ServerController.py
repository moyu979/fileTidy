import grpc_protobuf.Server_pb2 as Server_pb2
import grpc_protobuf.Server_pb2_grpc as Server_pb2_grpc

import os
import sqlite3

from func import vars
from func.tools import _fileTime

from Server.func.tools.DisKOperation import *
class ServerServicer(Server_pb2_grpc.Server):
    def TestAccess(self,request,context):
        print(f"received request with info {request.requestInfo}")
        return Server_pb2.TestAccessAnswer(answerInfo="success")

    def GetChecking(self,request,context):
        print(request.checkId)
        if request.checkId!="":
            if request.checkId in vars.nowChecking:
                respones=Server_pb2.CheckResult()
                respones.result=0
                respones.checkId.append(request.checkId)
                respones.checkInfo.append(vars.nowChecking[request.checkId])
            else:
                respones=Server_pb2.CheckResult()
                respones.result=1
        else:
            respones=Server_pb2.CheckResult()
            respones.result=0
            for k,v in vars.nowChecking.items():
                respones.checkId.append(k)
                respones.checkInfo.append(v)
        return respones