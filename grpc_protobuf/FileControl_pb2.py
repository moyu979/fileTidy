# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: grpc_protobuf/FileControl.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'grpc_protobuf/FileControl.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1fgrpc_protobuf/FileControl.proto\"(\n\x11TestAccessRequest\x12\x13\n\x0brequestInfo\x18\x01 \x01(\t\"&\n\x10TestAccessAnswer\x12\x12\n\nanswerInfo\x18\x01 \x01(\t\"J\n\x0e\x41\x64\x64\x46ileRequest\x12\x0e\n\x06\x64\x62path\x18\x01 \x01(\t\x12\x0c\n\x04path\x18\x02 \x01(\t\x12\x1a\n\x12\x44\x61taStroageMinimal\x18\x03 \x01(\t\"\x90\x01\n\rAddFileAnswer\x12%\n\x06result\x18\x01 \x01(\x0e\x32\x15.AddFileAnswer.Result\x12\x0c\n\x04info\x18\x05 \x01(\t\"J\n\x06Result\x12\x0b\n\x07success\x10\x00\x12\x0e\n\nnoSuchFile\x10\x01\x12\x11\n\rnoSuchStorage\x10\x02\x12\x10\n\x0cotherFailure\x10\x03\x32n\n\x0b\x46ileControl\x12\x33\n\nTestAccess\x12\x12.TestAccessRequest\x1a\x11.TestAccessAnswer\x12*\n\x07\x41\x64\x64\x46ile\x12\x0f.AddFileRequest\x1a\x0e.AddFileAnswerb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'grpc_protobuf.FileControl_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_TESTACCESSREQUEST']._serialized_start=35
  _globals['_TESTACCESSREQUEST']._serialized_end=75
  _globals['_TESTACCESSANSWER']._serialized_start=77
  _globals['_TESTACCESSANSWER']._serialized_end=115
  _globals['_ADDFILEREQUEST']._serialized_start=117
  _globals['_ADDFILEREQUEST']._serialized_end=191
  _globals['_ADDFILEANSWER']._serialized_start=194
  _globals['_ADDFILEANSWER']._serialized_end=338
  _globals['_ADDFILEANSWER_RESULT']._serialized_start=264
  _globals['_ADDFILEANSWER_RESULT']._serialized_end=338
  _globals['_FILECONTROL']._serialized_start=340
  _globals['_FILECONTROL']._serialized_end=450
# @@protoc_insertion_point(module_scope)
