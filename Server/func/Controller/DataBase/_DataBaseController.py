import DataBase_pb2 as DataBase_pb2
import DataBase_pb2_grpc as DataBase_pb2_grpc
import os
import sqlite3
from func import vars
from func.tools import _fileTime
from func.tools.DisKOperation import *
from func.tools.DisKOperation import *
from func.tools.decorators import *

from . import InitDatabase
from . import AddVolume,AddPhysicalStorage
from . import GetDisk,GetVolume
from . import UpdateDisk,UpdateVolume
@decorate_class_methods
class DataBaseServicer(DataBase_pb2_grpc.DataBase):

    def InitDataBase(self,request,context):
        return InitDatabase.initDatabase(request,context)

    def GetDisk(self,request,context):
        return GetDisk.getDisk(request,context)

    def GetVolume(self,request,context):
        return GetVolume.getVolume(request,context)

    def AddDisk(self,request,context):
        return AddPhysicalStorage.addPhysicalStorage(request,context)
  
    def AddVolume(self,request,context):
        return AddVolume.addVolume(request,context)

    def UpdateDisk(self,request,context):
        return UpdateDisk.updateDisk(request,context)

    def UpdateVolume(self,request,context):
        return UpdateVolume.updateVolume(request)