from __future__ import annotations

import traceback
from http import HTTPStatus
from logging import Logger, getLogger

import yaml
from aiohttp import web
from jinja2.exceptions import TemplateSyntaxError, UndefinedError

from ...flow_utils import FlowUtils
from ...utils.util import Util as Utils
from ..base import get_flow_utils, routes
from ..responses import json_response

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
async def check_template_2(request: web.Request) -> web.Response:
    """
    ---
    summary: Check jinja syntax
    description: Check if the provided jinja template is valid
    tags:
        - Mis
    requestBody:
        required: true
        content:
            application/x-www-form-urlencoded:
                schema:
                    type: object
                    properties:
                        template:
                            type: string
                            description: The jinja template to be checked
                            example: "Hello {{ name }}"
                        variables:
                            type: string
                            description: >
                                The variables to be used in the template, in `yaml` or `json` format
                            example: "{'name': 'world'}"
                    required:
                        - template
    responses:
        '200':
            $ref: '#/components/responses/CheckTemplateSuccess'
        '400':
            $ref: '#/components/responses/CheckTemplateBadRequest'
        '422':
            $ref: '#/components/responses/CheckTemplateUnprocessable'
    """

    trace_id = Utils.generate_uuid()
    dict_variables = {}

    try:
        data = await request.post()
    except Exception as e:
        return json_response(
            status=HTTPStatus.BAD_REQUEST,
            message=f"Error reading data: {e}",
        )

    template = data.get("template")
    variables = data.get("variables")

    log.info(f"({trace_id}) -> Checking jinja template with data: {data}")

    if not template:
        return json_response(
            status=HTTPStatus.BAD_REQUEST,
            message="Template is required",
        )

    if variables:
        try:
            dict_variables = yaml.safe_load(variables)
        except Exception as e:
            log.exception(e)
            return json_response(
                status=HTTPStatus.BAD_REQUEST,
                message=f"Error parsing variables: {e}",
            )
        else:
            if not isinstance(dict_variables, dict):
                return json_response(
                    status=HTTPStatus.BAD_REQUEST,
                    message="Variables must be a dictionary",
                )
    try:
        rendered_data = Utils.render_data(
            data=template, default_variables=dict_variables, return_errors=True
        )
    except TemplateSyntaxError as e:
        return json_response(
            status=HTTPStatus.UNPROCESSABLE_ENTITY,
            message={
                "func_name": e.name,
                "filename": e.filename if e.filename else "<template>",
                "line": e.lineno,
                "error": e.message,
            },
        )
    except UndefinedError as e:
        tb_list = traceback.extract_tb(e.__traceback__)
        traceback_info = tb_list[-1]

        func_name = traceback_info.name
        filename = traceback_info.filename
        line = traceback_info.lineno

        return json_response(
            status=HTTPStatus.UNPROCESSABLE_ENTITY,
            message={
                "func_name": func_name,
                "filename": filename,
                "line": line,
                "error": str(e),
            },
        )
    except Exception as e:
        return json_response(
            status=HTTPStatus.BAD_REQUEST,
            message=str(e),
        )

    return json_response(
        status=HTTPStatus.OK,
        message="Template rendered successfully",
        data=rendered_data,
    )
