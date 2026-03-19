import asyncio
from logging import Logger, getLogger

from aioagi.ami.action import AMIAction
from aioagi.ami.manager import AMIManager
from aioagi.ami.message import AMIMessage
from aiohttp import web

from ..base import get_config, routes
from ..responses import resp
from ..util import generate_uuid

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
    phone = data.get("phone")
    name = data.get("name")
    variables = data.get("variables", {})

    channel = config["ami.originate_command.channel"]
    context = config["ami.originate_command.context"]
    priority = config["ami.originate_command.priority"]
    timeout = config["ami.originate_command.timeout"]

    variables["TELEFONO"] = phone
    variables["CLIENT_NAME"] = name
    variables["CAMPAIGN"] = config["ami.originate_command.campaign"]
    variables["SUBCAMPAIGN"] = config["ami.originate_command.subcampaign"]

    try:
        action = AMIAction(
            {
                "Action": "Originate",
                "Channel": f"{channel}/{phone}",
                "Context": context,
                "Exten": phone,
                "Priority": priority,
                "CallerID": phone,
                "Timeout": str(timeout),
                "Variable": [f"{key.upper()}={value}" for key, value in variables.items()],
                "Async": "true",
            }
        )

        result: AMIMessage = await asyncio.wait_for(
            manager.send_action(action), timeout=config["ami.reconnect_delay"]
        )
    except asyncio.TimeoutError as e:
        return resp.internal_error("Originate timed out", uuid, log)
    except Exception as e:
        return resp.internal_error(e, uuid, log)

    formatted_result = {k: v for k, v in result.items()}
    log.debug(f"({uuid}) -> Result: {formatted_result}")
    return resp.success_response(message="Originate successfully queued", uuid=uuid)
