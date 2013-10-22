from account_pb2 import *
from hero_pb2 import *
from world_pb2 import *
from character_pb2 import *

RESPONSE_NOTIFY_TYPE = {
    "CommandResponse": 50,
    "StartGameResponse": 101,
    "GetServerListResponse": 104,
    "RegisterResponse": 106,
    "CharacterNotify": 202,
    "HeroNotify": 300,
    "AddHeroNotify": 301,
    "RemoveHeroNotify": 303,
    "UpdateHeroNotify": 304,
}

REQUEST_TYPE = {
    100: "StartGameRequest",
    102: "GetServerListRequest",
    105: "RegisterRequest",
    200: "CreateCharacterRequest",
}

REQUEST_TYPE_REV = {
    "StartGameRequest": 100,
    "GetServerListRequest": 102,
    "RegisterRequest": 105,
    "CreateCharacterRequest": 200,
}

