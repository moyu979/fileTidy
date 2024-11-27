import Server_pb2

from func import vars

def testAccess(request,context):
    return Server_pb2.TestAccessAnswer(answerInfo=f"connect to {vars.data["serverid"]} success")