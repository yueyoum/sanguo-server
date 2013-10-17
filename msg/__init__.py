from account_pb2 import *
from world_pb2 import *

RESPONSE_NOTIFY_TYPE = {
    "StartGameResponse": 101,
    "GetServerListResponse": 104,
}

REQUEST_TYPE = {
    100: ["StartGameRequest", "POST"],
    102: ["GetServerListRequest", "POST"],
}

REQUEST_TYPE_REV = {
    "StartGameRequest": 100,
    "GetServerListRequest": 102,
}

