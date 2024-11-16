import grpc_protobuf.Server_pb2 as Server_pb2
import grpc_protobuf.Server_pb2_grpc as Server_pb2_grpc
import threading
import os
import sqlite3

from func import vars
from func.tools import _fileTime
from func.tools.decorators import *

from Server.func.tools.DisKOperation import *
class ServerServicer(Server_pb2_grpc.Server):
    @say_begin_and_end
    def TestAccess(self,request,context):
        print(vars.data["serverid"],111)
        current_thread = threading.current_thread()
        print(f"当前线程名: {current_thread.name}")
        print(f"当前线程ID: {current_thread.ident}")
        print(f"当前进程ID: {os.getpid()}")
        print(f"当前模块名: {__name__}")
        print(vars.data)
        print(f"received request with info \"{request.requestInfo}\"")
        return Server_pb2.TestAccessAnswer(answerInfo=f"connect to {vars.data["serverid"]} success")
    # @say_begin_and_end
    # def GetChecking(self,request,context):
    #     print(f"received GetChecking request with id \"{request.checkId}\"")
    #     if request.checkId!="":
    #         if request.checkId in vars.nowChecking:
    #             respones=Server_pb2.CheckResult()
    #             respones.result=0
    #             respones.checkId.append(request.checkId)
    #             respones.checkInfo.append(vars.nowChecking[request.checkId])
    #         else:
    #             respones=Server_pb2.CheckResult()
    #             respones.result=1
    #     else:
    #         respones=Server_pb2.CheckResult()
    #         respones.result=0
    #         for k,v in vars.nowChecking.items():
    #             respones.checkId.append(k)
    #             respones.checkInfo.append(v)
    #     return respones