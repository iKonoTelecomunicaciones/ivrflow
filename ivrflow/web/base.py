from __future__ import annotations

from aiohttp import web

from .. import VERSION
from ..config import Config
from ..flow_utils import FlowUtils

_config: Config | None = None
_flow_utils: FlowUtils | None = None

routes: web.RouteTableDef = web.RouteTableDef()


def set_config(config: Config, flow_utils: FlowUtils) -> None:
    global _config
    global _flow_utils

    _config = config
    _flow_utils = flow_utils


def get_config() -> Config:
    return _config


def get_flow_utils() -> FlowUtils:
    return _flow_utils


@routes.get("/version")
async def get_version(_: web.Request) -> web.Response:
    return web.json_response({"version": VERSION})
