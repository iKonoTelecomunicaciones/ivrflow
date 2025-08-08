from __future__ import annotations

from logging import Logger, getLogger

from aiohttp import web

from ...db.flow import Flow as DBFlow
from ...db.module import Module as DBModule
from ...utils import Util
from ..base import routes
from ..docs.node import get_node_doc
from ..responses import resp
from ..util import docstring, generate_uuid

log: Logger = getLogger("ivrflow.api.node")


@routes.get("/v1/{flow_id}/node/{id}", allow_head=False)
@docstring(get_node_doc)
async def get_node(request: web.Request) -> web.Response:
    uuid = generate_uuid()
    log.info(f"({uuid}) -> '{request.method}' '{request.path}' Getting node")

    module_name = Util.convert_to_bool(request.query.get("module_name", True))
    node_id = request.match_info["id"]

    try:
        flow_id = int(request.match_info["flow_id"])

        if not await DBFlow.check_exists(flow_id):
            return resp.not_found(f"Flow with ID {flow_id} not found in the database", uuid)

        node = await DBModule.get_node_by_id(flow_id, node_id, module_name)
    except (KeyError, ValueError):
        return resp.bad_request("Invalid or missing flow ID", uuid)
    except Exception as e:
        return resp.internal_error(e, uuid, log)

    if not node:
        return resp.not_found(f"Node with ID '{node_id}' not found in the database", uuid)

    return resp.success_response("", uuid, node)
