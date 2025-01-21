from __future__ import annotations

import asyncio
import logging

from aiohttp import web
from aiohttp.abc import AbstractAccessLogger

from ..config import config
from ..flow_utils import FlowUtils
from .management_api import ManagementAPI


class AccessLogger(AbstractAccessLogger):
    def log(self, request: web.Request, response: web.Response, time: int):
        self.logger.info(
            f'{request.remote} "{request.method} {request.path} '
            f"{response.status} {response.body_length} "
            f'in {round(time, 4)}s"'
        )


class APIServer:
    log: logging.Logger = logging.getLogger("ivrflow.server")

    def __init__(self, loop: asyncio.AbstractEventLoop, flow_utils: FlowUtils) -> None:
        management_api = ManagementAPI(flow_utils=flow_utils)
        self.app = web.Application(loop=loop, client_max_size=100 * 1024 * 1024)
        self.app.add_subapp(config["server.base_path"], management_api.app)
        self.runner = web.AppRunner(self.app, access_log_class=AccessLogger)

    async def start(self) -> None:
        await self.runner.setup()
        site = web.TCPSite(self.runner, config["server.hostname"], config["server.port"])
        await site.start()
        self.log.info(f"Listening on {site.name}")

    async def stop(self) -> None:
        await self.runner.shutdown()
        await self.runner.cleanup()
