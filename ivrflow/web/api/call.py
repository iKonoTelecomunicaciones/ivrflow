from logging import Logger, getLogger

from aioagi.ami.action import AMIAction
from aioagi.ami.manager import AMIManager
from aioagi.ami.message import AMIMessage
from aiohttp import web

from ..base import get_config, routes
from ..responses import resp
from ..util import docstring, generate_uuid

log: Logger = getLogger("ivrflow.api.call")


@routes.post("/v1/call")
async def call(request: web.Request) -> web.Response:
    uuid = generate_uuid()
    config = get_config()
    log.info(f"({uuid}) -> '{request.method}' '{request.path}' Call")

    manager: AMIManager = request.config_dict.get("ami_manager")
    if not manager:
        return resp.internal_error("AMI manager not found", uuid)

    data = await request.json()
    exten = data.get("phone")
    name = data.get("name")
    variables = data.get("variables", {})

    channel = config["ami.originate_command.channel"]
    context = config["ami.originate_command.context"]
    priority = config["ami.originate_command.priority"]
    timeout = config["ami.originate_command.timeout"]

    variables["TELEFONO"] = exten
    variables["CLIENT_NAME"] = name
    variables["CAMPAIGN"] = config["ami.originate_command.campaign"]
    variables["SUBCAMPAIGN"] = config["ami.originate_command.subcampaign"]

    action = AMIAction(
        {
            "Action": "Originate",
            "Channel": channel,
            "Context": context,
            "Exten": exten,
            "Priority": priority,
            "CallerID": exten,
            "Timeout": str(timeout),
            "Variable": [f"{key.upper()}={value}" for key, value in variables.items()],
            "Async": "true",
        }
    )

    result: AMIMessage = await manager.send_action(action)
    formatted_result = {k: v for k, v in result.items()}
    return resp.success_response(data=formatted_result, uuid=uuid)
