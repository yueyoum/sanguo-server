from account_pb2 import *
from hero_pb2 import *
from world_pb2 import *
from character_pb2 import *
from item_pb2 import *
from formation_pb2 import *
from battle_pb2 import *

RESPONSE_NOTIFY_TYPE = {
    "CommandResponse": 50,
    "VersionCheckResponse": 52,
    "StartGameResponse": 101,
    "GetServerListResponse": 104,
    "RegisterResponse": 106,
    "CreateCharacterResponse": 201,
    "CharacterNotify": 202,
    "HeroNotify": 300,
    "AddHeroNotify": 301,
    "RemoveHeroNotify": 303,
    "UpdateHeroNotify": 304,
    "GetHeroPanelNotify": 305,
    "GetHeroResponse": 321,
    "MergeHeroResponse": 323,
    "SetFormationResponse": 401,
    "FormationNotify": 402,
    "AddSocketNotify": 403,
    "SocketNotify": 404,
    "SetSocketResponse": 406,
    "AlreadyStageNotify": 500,
    "CurrentStageNotify": 501,
    "NewStageNotify": 502,
    "PVEResponse": 601,
    "EquipNotify": 700,
    "AddEquipNotify": 701,
    "RemoveEquipNotify": 702,
    "UpdateEquipNotify": 703,
    "StrengthEquipResponse": 705,
    "SellEquipResponse": 707,
    "GemNotify": 750,
    "AddGemNotify": 751,
    "UpdateGemNotify": 752,
    "RemoveGemNotify": 753,
    "MergeGemResponse": 755,
    "EmbedGemResponse": 757,
    "UnEmbedGemResponse": 759,
}

REQUEST_TYPE = {
    51: "VersionCheckRequest",
    100: "StartGameRequest",
    102: "GetServerListRequest",
    105: "RegisterRequest",
    200: "CreateCharacterRequest",
    320: "GetHeroRequest",
    322: "MergeHeroRequest",
    400: "SetFormationRequest",
    405: "SetSocketRequest",
    600: "PVERequest",
    704: "StrengthEquipRequest",
    706: "SellEquipRequest",
    754: "MergeGemRequest",
    756: "EmbedGemRequest",
    758: "UnEmbedGemRequest",
}

REQUEST_TYPE_REV = {
    "VersionCheckRequest": 51,
    "StartGameRequest": 100,
    "GetServerListRequest": 102,
    "RegisterRequest": 105,
    "CreateCharacterRequest": 200,
    "GetHeroRequest": 320,
    "MergeHeroRequest": 322,
    "SetFormationRequest": 400,
    "SetSocketRequest": 405,
    "PVERequest": 600,
    "StrengthEquipRequest": 704,
    "SellEquipRequest": 706,
    "MergeGemRequest": 754,
    "EmbedGemRequest": 756,
    "UnEmbedGemRequest": 758,
}

