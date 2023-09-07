from typing import NewType

from mautrix.types import SerializableEnum

ChannelUniqueID = NewType("ChannelUniqueID", str)


class NodeType(SerializableEnum):
    http_request = "http_request"
    playback = "playback"
    switch = "switch"
    get_data = "get_data"


class MiddlewareType(SerializableEnum):
    jwt = "jwt"
    basic = "basic"
    tts = "tts"
