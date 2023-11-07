from __future__ import annotations

import asyncio
import sys
from logging import Logger, getLogger
from typing import Dict

from aioagi import runner
from aioagi.app import AGIApplication
from aioagi.exceptions import AGIAppError
from aioagi.urldispathcer import AGIView
from aiohttp import ClientSession, TraceConfig
from mautrix.util.async_db import Database, DatabaseException

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

log: Logger = getLogger("ivrflow.main")


class IVRFlow(AGIView):
    db: Database
    http_client: ClientSession
    flow_utils: "FlowUtils" | None = None

    async def sip(self):
        await self.algorithm()

    async def local(self):
        await self.algorithm()

    async def dahdi(self):
        await self.algorithm()

    async def post_init(self) -> (Flow, Channel):
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
            log.debug(f"Channel {channel.channel_uniqueid} does not have a node")
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
        log.debug("Starting database...")
        try:
            await cls.db.start()
        except DatabaseException as e:
            log.critical("Failed to initialize database", exc_info=e)
            if e.explanation:
                log.info(e.explanation)
            sys.exit(25)

    @classmethod
    def init_http_client(cls) -> None:
        trace_config = TraceConfig()
        trace_config.on_request_start.append(start_auth_middleware)
        trace_config.on_request_end.append(end_auth_middleware)
        cls.http_client = ClientSession(trace_configs=[trace_config])

    @classmethod
    async def start(cls) -> None:
        IVRFlow.prepare_db()
        await IVRFlow.start_db()
        IVRFlow.init_http_client()
        cls.flow_utils = FlowUtils()
        if cls.flow_utils:
            asyncio.create_task(cls.start_email_connections())

    @classmethod
    async def stop(cls) -> None:
        await cls.http_client.close()

    @property
    def flow_path(self):
        return self.request.path.strip("/")


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(IVRFlow.start())
        app = AGIApplication()
        app.router.add_route("*", "/{key:.+}", IVRFlow)
        runner.run_app(app)
    finally:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(IVRFlow.stop())
