import asyncio
import sys
from logging import Logger, getLogger

from aioagi import runner
from aioagi.app import AGIApplication
from aioagi.log import agi_server_logger as Logger
from aioagi.urldispathcer import AGIView
from mautrix.util.async_db import Database, DatabaseException

from .channel import Channel
from .config import config
from .db import init as init_db
from .db import upgrade_table
from .db.channel import ChannelState
from .flow import Flow
from .nodes import Base
from .repository import Flow as FlowModel

log: Logger = getLogger("ivrflow.main")


class IVRFlow(AGIView):
    db: Database

    async def sip(self):
        await self.algorithm()

    async def local(self):
        await self.algorithm()

    async def dahdi(self):
        await self.algorithm()

    async def algorithm(self, channel: Channel = None):
        Base.init_cls(config=config, asterisk_conn=self.request)
        channel = await Channel.get_by_channel_uniqueid(
            channel_uniqueid=self.request.headers["agi_channel"]
        )
        flow_model = FlowModel.load_flow(self.flow_path)
        flow = Flow(flow_data=flow_model)
        node = flow.node(channel=channel)

        if node is None:
            log.debug(f"Room {channel.channel_uniqueid} does not have a node")
            await channel.update_ivr(node_id="start")
            return

        log.debug(
            f"The [channel: {channel.channel_uniqueid}] [node: {node.id}] [state: {channel.state}]"
        )

        await node.run()

        if channel.state == ChannelState.END:
            log.debug(f"The channel {channel.channel_uniqueid} has terminated the flow")
            await channel.update_ivr(node_id=ChannelState.START)
            return

        await self.algorithm(channel=channel)

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
    async def start(cls) -> None:
        IVRFlow.prepare_db()
        await IVRFlow.start_db()

    @property
    def flow_path(self):
        return self.request.path.strip("/")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(IVRFlow.start())
    app = AGIApplication()
    app.router.add_route("*", "/{key:.+}", IVRFlow)
    runner.run_app(app)
