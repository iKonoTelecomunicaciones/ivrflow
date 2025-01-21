from __future__ import annotations

import asyncio
import sys
from logging import Logger, getLogger
from time import time
from typing import Dict, Tuple

from aioagi import runner
from aioagi.app import AGIApplication
from aioagi.exceptions import AGIAppError
from aioagi.urldispathcer import AGIView
from aiohttp import ClientSession, TraceConfig
from mautrix.util.async_db import Database, DatabaseException

try:
    import uvloop
except ImportError:
    uvloop = None

from . import VERSION
from .channel import Channel
from .config import config
from .db import init as init_db
from .db import upgrade_table
from .db.channel import ChannelState
from .email_client import EmailClient
from .flow import Flow
from .flow_utils import EmailServer, FlowUtils
from .http_middleware import end_auth_middleware, start_auth_middleware
from .models import Flow as FlowModel
from .nodes import Base
from .web import APIServer

log: Logger = getLogger("ivrflow.main")


class IVRFlow(AGIView):
    loop: asyncio.AbstractEventLoop
    db: Database
    http_client: ClientSession
    flow_utils: "FlowUtils" | None = None
    management_api: APIServer

    @property
    def flow_path(self):
        return self.request.path.strip("/")

    @classmethod
    def prepare_db(cls) -> None:
        cls.db = Database.create(
            config["ivrflow.database"],
            upgrade_table=upgrade_table,
            db_args=config["ivrflow.database_opts"],
            owner_name="ivrflow",
        )
        init_db(cls.db)

    @classmethod
    async def start_email_connections(self):
        log.debug("Starting email clients...")
        email_servers: Dict[str, EmailServer] = self.flow_utils.get_email_servers()
        for key, server in email_servers.items():
            if server.server_id.lower().startswith("sample"):
                continue

            email_client = EmailClient(
                server_id=server.server_id,
                host=server.host,
                port=server.port,
                username=server.username,
                password=server.password,
                start_tls=server.start_tls,
            )
            await email_client.login()
            email_client._add_to_cache()

    @classmethod
    async def start_db(cls) -> None:
        log.info("Starting database...")
        try:
            await cls.db.start()
        except DatabaseException as e:
            log.exception("Failed to initialize database", exc_info=e)
            if e.explanation:
                log.info(e.explanation)
            sys.exit(25)

    @classmethod
    def init_http_client(cls) -> None:
        trace_config = TraceConfig()
        trace_config.on_request_start.append(start_auth_middleware)
        trace_config.on_request_end.append(end_auth_middleware)
        cls.http_client = ClientSession(trace_configs=[trace_config], loop=cls.loop)

    @classmethod
    def init_management_api(cls) -> None:
        cls.management_api = APIServer(flow_utils=cls.flow_utils, loop=cls.loop)

    @classmethod
    async def stop(cls) -> None:
        log.info("Stopping http client...")
        await cls.http_client.close()

    @classmethod
    async def start(cls):
        await cls.start_db()
        cls.flow_utils = FlowUtils()
        if cls.flow_utils:
            asyncio.create_task(cls.start_email_connections())
        await cls.management_api.start()

    @classmethod
    def init(cls):
        cls._prepare()
        cls.loop.run_until_complete(cls.start())

    @classmethod
    def _prepare(cls):
        start_ts = time()

        log.info(f"Initializing IVRFlow {VERSION}")
        try:
            cls.prepare()
        except Exception:
            log.critical("Unexpected error in initialization", exc_info=True)
            sys.exit(1)
        end_ts = time()
        log.info(f"Initialization complete in {round(end_ts - start_ts, 2)} seconds")

    @classmethod
    def prepare(cls):
        cls.prepare_loop()
        cls.prepare_db()
        cls.init_http_client()
        cls.init_management_api()

    @classmethod
    def prepare_loop(cls) -> None:
        """Init lifecycle method where the asyncio event loop is created."""

        if uvloop is not None:
            uvloop.install()
            log.debug("Using uvloop for asyncio")

        cls.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls.loop)

    async def sip(self):
        await self.algorithm()

    async def local(self):
        await self.algorithm()

    async def dahdi(self):
        await self.algorithm()

    async def post_init(self) -> Tuple[Flow, Channel]:
        Base.init_cls(config=config, asterisk_conn=self.request, session=self.http_client)
        channel = await Channel.get_by_channel_uniqueid(
            channel_uniqueid=self.request.headers["agi_uniqueid"]
        )
        flow_model = FlowModel.load_flow(self.flow_path)
        flow = Flow(flow_data=flow_model, flow_utils=self.flow_utils)

        return flow, channel

    async def algorithm(self) -> None:
        flow: Flow
        channel: Channel

        flow, channel = await self.post_init()

        node = flow.node(channel=channel)

        if node is None:
            log.debug(f"Channel {channel.channel_uniqueid} does not have a node [{node.id}]")
            await channel.update_ivr(node_id="start")
            return

        log.debug(
            f"The [channel: {channel.channel_uniqueid}] [node: {node.id}] [state: {channel.state}]"
        )

        try:
            await node.run()
        except AGIAppError as e:
            log.error(f"Error in node {node.id}", exc_info=e)
            return

        if channel.state == ChannelState.END:
            log.debug(f"The channel {channel.channel_uniqueid} has terminated the flow")
            await channel.update_ivr(node_id=ChannelState.START)
            return

        await self.algorithm()


if __name__ == "__main__":
    try:
        IVRFlow.init()
        app = AGIApplication()
        app.router.add_route("*", "/{key:.+}", IVRFlow)
        runner.run_app(app)
    finally:
        log.info("Stopping IVRFlow...")
        loop = asyncio.new_event_loop()
        loop.run_until_complete(IVRFlow.stop())
        loop.close()
        log.info("IVRFlow has stopped")
