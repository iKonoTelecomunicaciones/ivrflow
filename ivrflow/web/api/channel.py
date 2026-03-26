from __future__ import annotations

from logging import Logger, getLogger

from aiohttp import web

from ...db.channel import Channel
from ..base import routes
from ..docs.channel import get_variables_doc
from ..responses import resp
from ..util import docstring, generate_uuid

log: Logger = getLogger("ivrflow.api.misc")


@routes.get("/v1/room/{uniqueid}/get_variables", allow_head=False)
@docstring(get_variables_doc)
async def get_variables(request: web.Request) -> web.Response:
    uuid = generate_uuid()
    log.info(f"({uuid}) -> '{request.method}' '{request.path}' Getting variables")

    uniqueid = request.match_info["uniqueid"]
    scopes = request.query.getall("scopes", ["route", "hook"])
    response = {}

    try:
        channel: Channel | None = await Channel.get_by_channel_uniqueid(channel_uniqueid=uniqueid)
        if not channel:
            return resp.not_found(f"channel_uniqueid '{uniqueid}' not found", uuid)

        for scope in scopes:
            match scope:
                case "route":
                    response[scope] = channel._variables.get(scope, {})
                case "hook":
                    response[scope] = channel._variables.get(scope, {})
                case _:
                    log.warning(f"({uuid}) -> Invalid scope: {scope}, skipping")

    except Exception as e:
        return resp.internal_error(e, uuid, log)

    return (
        resp.success_response(data=response, uuid=uuid)
        if response
        else resp.not_found("Scopes not found", uuid)
    )
