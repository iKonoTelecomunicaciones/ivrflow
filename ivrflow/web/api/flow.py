from __future__ import annotations

from http import HTTPStatus
from json import JSONDecodeError
from typing import Dict

from aiohttp import web

from ...db.flow import Flow as DBFlow
from ..base import routes
from ..responses import json_response


# Update or create new flow
@routes.put("/v1/flow")
async def create_or_update_flow(request: web.Request) -> web.Response:
    """
    ---
    summary: Creates a new flow or update it if exists.
    tags:
        - Flow

    requestBody:
        required: false
        description: A json with `id` and `flow` keys.
                     `id` is the flow ID to update, `flow` is the flow content.
                     send only `flow` to create a new flow.
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        id:
                            type: integer
                        flow:
                            type: object
                    required:
                        - flow
                    example:
                        id: 1
                        flow:
                            menu:
                                flow_variables:
                                    var1: "value1"
                                    var2: "value2"
                                nodes:
                                    - id: play
                                      type: playback
                                      file: "vm-extension"
                                      escape_digits: 0
                                      sample_offset: 0
                                      o_connection: next_node
    responses:
        '200':
            $ref: '#/components/responses/CreateUpdateFlowSuccess'
        '400':
            $ref: '#/components/responses/CreateUpdateFlowBadRequest'
    """
    try:
        data: Dict = await request.json()
    except JSONDecodeError:
        return json_response(HTTPStatus.BAD_REQUEST, "Request body is not JSON.")

    flow_id = data.get("id")
    incoming_flow = data.get("flow")

    if not incoming_flow:
        return json_response(HTTPStatus.BAD_REQUEST, "Parameter flow is required")

    if flow_id:
        flow = await DBFlow.get_by_id(flow_id)
        flow.flow = incoming_flow
        await flow.update()

        message = "Flow updated successfully"
        status = HTTPStatus.OK
    else:
        new_flow = DBFlow(flow=incoming_flow)
        flow_id = await new_flow.insert()
        message = "Flow created successfully"
        status = HTTPStatus.CREATED

    return json_response(status=status, message=message, data={"flow_id": flow_id})


@routes.get("/v1/flow/{flow_id}", allow_head=False)
async def get_flow(request: web.Request) -> web.Response:
    """
    ---
    summary: Get flow by ID or client MXID.
    tags:
        - Flow

    parameters:
        - name: flow_id
          in: path
          required: true
          description: The room ID to set variables for
          schema:
            type: integer
          example: 1

    responses:
        '200':
            $ref: '#/components/responses/GetFlowSuccess'
        '404':
            $ref: '#/components/responses/GetFlowNotFound'
    """
    flow_id = request.match_info["flow_id"]
    flow = await DBFlow.get_by_id(int(flow_id))

    if not flow:
        return json_response(
            status=HTTPStatus.NOT_FOUND, message=f"Flow with ID {flow_id} not found"
        )

    data = flow.serialize()

    return json_response(status=HTTPStatus.OK, data=data)
