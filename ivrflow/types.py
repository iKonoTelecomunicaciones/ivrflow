from typing import NewType

from mautrix.types import SerializableEnum

ChannelUniqueID = NewType("ChannelUniqueID", str)


class NodeType(SerializableEnum):
    http_request = "http_request"
    playback = "playback"
    switch = "switch"
    get_data = "get_data"
    set_variable = "set_variable"
    record = "record"
    hangup = "hangup"
    set_music = "set_music"
    verbose = "verbose"
    set_callerid = "set_callerid"
    email = "email"
    exec_app = "exec_app"
    get_full_variable = "get_full_variable"
    database_del = "database_del"


class MiddlewareType(SerializableEnum):
    jwt = "jwt"
    basic = "basic"
    tts = "tts"
    asr = "asr"
