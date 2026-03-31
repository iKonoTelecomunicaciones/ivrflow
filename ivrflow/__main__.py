from __future__ import annotations

import asyncio
import sys
from logging import Logger, getLogger
from time import time
from typing import Dict, Tuple

from aioagi import runner
from aioagi.app import AGIApplication
from aioagi.exceptions import AGIAppError, AGIHangup
from aioagi.urldispathcer import AGIView
from aiohttp import ClientSession, TraceConfig
from mautrix.util.async_db import Database, DatabaseException

from .safe_ami_manager import SafeAMIManager

try:
    import uvloop  # type: ignore
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
from .nodes import Base, Email, HTTPRequest, NoOp, SetVars, Switch
from .web import APIServer

log: Logger = getLogger("ivrflow.main")


class IVRFlow(AGIView):
    loop: asyncio.AbstractEventLoop
    db: Database
    http_client: ClientSession
    flow_utils: "FlowUtils" | None = None
    management_api: APIServer
    ami_connect_task: asyncio.Task | None = None
    ALLOWED_AFTER_HANGUP_NODES = (HTTPRequest, Switch, SetVars, Email, NoOp)

    @property
    def flow_name(self):
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
        cls.management_api = APIServer(
            flow_utils=cls.flow_utils, loop=cls.loop, ami_manager=cls.ami_manager
        )

    @classmethod
    def init_flow_complements(cls):
        cls.flow_utils = FlowUtils()
        Flow.init_cls(flow_utils=cls.flow_utils)

    @classmethod
    async def stop(cls) -> None:
        if config["ami.enabled"]:
            log.info("Stopping AMI...")
            if cls.ami_connect_task and not cls.ami_connect_task.done():
                cls.ami_connect_task.cancel()
                try:
                    await cls.ami_connect_task
                except asyncio.CancelledError:
                    pass
            await cls.ami_manager.close()
        log.info("Stopping http client...")
        await cls.http_client.close()

    @classmethod
    async def start(cls):
        if config["ami.enabled"]:
            cls.ami_connect_task = asyncio.create_task(cls.ami_manager.connect())
        await cls.start_db()
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
        cls.init_flow_complements()
        cls.prepare_loop()
        cls.prepare_db()
        cls.init_http_client()
        cls.prepare_ami()
        cls.init_management_api()

    @classmethod
    def prepare_loop(cls) -> None:
        """Init lifecycle method where the asyncio event loop is created."""

        if uvloop is not None:
            uvloop.install()
            log.debug("Using uvloop for asyncio")

        cls.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls.loop)

        if config["ivrflow.enable_asyncio_debug"]:
            log.warning("Running in debug mode")
            cls.loop.set_debug(True)

    @classmethod
    def prepare_ami(cls) -> None:
        if config["ami.enabled"]:
            cls.ami_manager = SafeAMIManager(
                app=cls,
                title="AMI",
                host=config["ami.hostname"],
                port=config["ami.port"],
                username=config["ami.username"],
                secret=config["ami.password"],
                reconnect_delay=float(config["ami.reconnect_delay"]),
            )
        else:
            cls.ami_manager = None

    async def sip(self):
        async with Base.agi_ctx(asterisk_conn=self.request, http_session=self.http_client):
            await self.algorithm()

    async def local(self):
        async with Base.agi_ctx(asterisk_conn=self.request, http_session=self.http_client):
            await self.algorithm()

    async def dahdi(self):
        async with Base.agi_ctx(asterisk_conn=self.request, http_session=self.http_client):
            await self.algorithm()

    async def post_init(self) -> Tuple[Flow, Channel]:
        Base.init_cls(config=config)
        uniqueid: str = self.request.headers["agi_uniqueid"]

        channel = await Channel.get_by_channel_uniqueid(channel_uniqueid=uniqueid)
        await channel.set_variable("uniqueid", uniqueid)

        flow = Flow()
        await flow.load_flow(self.flow_name)

        return flow, channel

    async def algorithm(self) -> None:
        flow: Flow
        channel: Channel

        flow, channel = await self.post_init()
        uid: str = channel.channel_uniqueid

        reason = "completed"
        node = None

        while channel.state != ChannelState.END:
            node = flow.node(channel=channel)
            if node is None:
                reason = "invalid_node"
                break

            if channel.state == ChannelState.HANGUP and not isinstance(
                node, self.ALLOWED_AFTER_HANGUP_NODES
            ):
                reason = "hangup_node_not_allowed"
                break

            try:
                log.debug(
                    f"[{uid}] Starting node: ({node.id}) state: ({channel.state}) type: ({node.type})"
                )
                await node.run()
            except (AGIAppError, AGIHangup) as e:
                hangup_var = "hook.on_hangup.node_id"
                next_node_id = await channel.get_variable(hangup_var)
                reason = "hangup_detected"

                log.warning(
                    f"[{uid}] Hangup detected in node: ({node.id}) next node: ({next_node_id})"
                )
                if not next_node_id:
                    reason = "on_hangup_node_not_found"
                    await channel.update_ivr(node_id=None, state=ChannelState.HANGUP)
                    break

                await channel.update_ivr(node_id=next_node_id, state=ChannelState.HANGUP)
            except Exception:
                reason = "unexpected_error"
                log.exception(f"[{uid}] Exception in algorithm")
                break

            log.debug(
                f"[{uid}] Finished node: ({node.id}) State: ({channel.state}) type: ({node.type})"
            )

        log.info(
            f"[{uid}] Flow finished reason ({reason}) "
            f"state ({channel.state}) node ({getattr(node, 'id', None)})"
        )


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
