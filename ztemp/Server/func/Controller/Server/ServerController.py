import Server_pb2 as Server_pb2
import Server_pb2_grpc as Server_pb2_grpc

from func.tools.decorators import *
from . import TestAccess
@decorate_class_methods
class ServerServicer(Server_pb2_grpc.Server):
    def TestAccess(self,request,context):
        return TestAccess.testAccess(request,context)