from __future__ import annotations

from json import JSONDecodeError
from logging import Logger, getLogger
from typing import Dict

from aiohttp import web

from ...db.flow import Flow as DBFlow
from ..base import routes
from ..docs.flow import create_or_update_flow_doc, get_flow_doc
from ..responses import resp
from ..util import docstring, generate_uuid

log: Logger = getLogger("ivrflow.api.flow")


# Update or create new flow
@routes.put("/v1/flow")
@docstring(create_or_update_flow_doc)
async def create_or_update_flow(request: web.Request) -> web.Response:
    uuid = generate_uuid()
    log.info(f"({uuid}) -> '{request.method}' '{request.path}' Creating or updating flow")

    try:
        data: Dict = await request.json()
    except JSONDecodeError:
        return resp.bad_request("Request body is not JSON.", uuid)

    flow_id = data.get("id")
    name: str = data.get("name")
    flow_vars = data.get("flow_vars")

    try:
        if flow_id:
            flow = await DBFlow.get_by_id(flow_id)
            if not flow:
                return resp.not_found(f"Flow with ID {flow_id} not found", uuid)

            if name:
                flow.name = name

            if flow_vars:
                flow.flow_vars = flow_vars

            await flow.update()
        else:
            if not name:
                return resp.bad_request("Parameter name is required", uuid)

            flow_exists = await DBFlow.get_by_name(name)
            if flow_exists:
                return resp.bad_request(f"Flow with name {name} already exists", uuid)

            new_flow = DBFlow(name=name, flow_vars=flow_vars)
            flow_id = await new_flow.insert()

            return resp.created("Flow created successfully", uuid)
    except Exception as e:
        return resp.internal_error(e, uuid, log)

    return resp.success_response("Flow updated successfully", uuid)


@routes.get("/v1/flow", allow_head=False)
@docstring(get_flow_doc)
async def get_flow(request: web.Request) -> web.Response:
    uuid = generate_uuid()
    log.info(f"({uuid}) -> '{request.method}' '{request.path}' Getting flow")

    flow_id = request.query.get("flow_id")
    flow_name = request.query.get("flow_name")

    if flow_id or flow_name:
        if flow_id:
            data = await DBFlow.get_by_id(int(flow_id))
            if not data:
                return resp.not_found(f"Flow with ID {flow_id} not found")
        else:
            data = await DBFlow.get_by_name(flow_name)
            if not data:
                return resp.not_found(f"Flow with name {flow_name} not found")
        data = data.serialize()
    else:
        data = {"flows": [{flow.pop("name"): flow for flow in await DBFlow.all()}]}

    return resp.success_response("", uuid, data=data)
