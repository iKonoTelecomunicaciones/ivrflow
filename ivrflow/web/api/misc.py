from __future__ import annotations

from http import HTTPStatus
from logging import Logger, getLogger

import yaml
from aiohttp import web

from ...flow_utils import FlowUtils
from ...utils.flags import RenderFlags
from ...utils.util import Util as Utils
from ..base import get_flow_utils, routes
from ..docs.misc import check_template_doc
from ..responses import json_response, resp
from ..util import docstring, generate_uuid

log: Logger = getLogger("ivrflow.api.misc")


@routes.get("/v1/mis/email_servers", allow_head=False)
async def get_id_email_servers(request: web.Request) -> web.Response:
    """
    ---
    summary: Get email servers registered in flow utils.
    tags:
        - Mis

    responses:
        '200':
            $ref: '#/components/responses/GetEmailServersSuccess'
    """

    name_email_servers = list(FlowUtils.email_servers_by_id.keys())
    return json_response(status=HTTPStatus.OK, data={"email_servers": name_email_servers})


@routes.get("/v1/mis/middlewares", allow_head=False)
async def get_id_middlewares(request: web.Request) -> web.Response:
    """
    ---
    summary: Get email servers registered in flow utils.
    tags:
        - Mis

    responses:
        '200':
            $ref: '#/components/responses/GetMiddlewaresSuccess'
    """

    flow_utils = get_flow_utils()
    middlewares = [
        {"id": middleware.id, "type": middleware.type}
        for middleware in flow_utils.data.middlewares
    ]
    return json_response(status=HTTPStatus.OK, data={"middlewares": middlewares})


@routes.post("/v1/mis/check_template")
@docstring(check_template_doc)
async def check_template(request: web.Request) -> web.Response:
    trace_id = generate_uuid()
    log.info(f"({trace_id}) -> '{request.method}' '{request.path}' Checking template")

    try:
        data = await request.post()
    except Exception as e:
        return resp.bad_request(f"Error reading data: {e}", trace_id)

    template = data.get("template")
    variables = data.get("variables")
    string_format = data.get("string_format", False)
    flags = data.get(
        "flags",
        {
            "REMOVE_QUOTES": True,
            "LITERAL_EVAL": True,
            "CONVERT_TO_TYPE": True,
            "CUSTOM_ESCAPE": False,
        },
    )

    try:
        flags = yaml.safe_load(flags)
    except Exception as e:
        pass
    finally:
        if not isinstance(flags, dict):
            return resp.bad_request("The format of the flags is not valid", trace_id)

    _flags = RenderFlags.RETURN_ERRORS
    for flag, enabled in flags.items():
        if enabled is True:
            _flags |= getattr(RenderFlags, flag)

    log.info(f"({trace_id}) -> Checking jinja template with data: {data}")

    if not template:
        return resp.bad_request("Template is required", trace_id)

    if variables:
        try:
            dict_variables = yaml.safe_load(variables)
        except Exception as e:
            log.exception(e)
            return resp.bad_request(f"Error format variables: {e}", trace_id)
        else:
            if not isinstance(dict_variables, dict):
                return resp.bad_request("The format of the variables is not valid", trace_id)
    try:
        if RenderFlags.CUSTOM_ESCAPE in _flags:
            dict_variables, changed = Utils.custom_escape(dict_variables, escape=False)
            _flags = _flags | RenderFlags.CUSTOM_UNESCAPE if changed else _flags

        new_render_data = Utils.recursive_render(template, dict_variables, flags=_flags)
    except Exception as e:
        return resp.internal_error(e, trace_id)

    response = {
        "rendered": new_render_data,
        **({"string_format": str(new_render_data)} if string_format else {}),
    }

    return resp.success_response(data=response, uuid=trace_id)
