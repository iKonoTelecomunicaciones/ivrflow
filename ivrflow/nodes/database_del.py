from typing import Dict

from ..channel import Channel, ChannelState
from ..models import DatabaseDel as DatabaseDelModel
from .base import Base


class DatabaseDel(Base):
    def __init__(
        self, default_variables: Dict, database_del_content: DatabaseDelModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(database_del_content.id)
        self.content: DatabaseDelModel = database_del_content

    @property
    def entries(self) -> str:
        return self.render_data(data=self.content.entries)

    @property
    def o_connection(self) -> str:
        return self.get_o_connection()

    async def run(self):
        self.log.info(f"[{self.channel.channel_uniqueid}] Entering database_del node {self.id}")
        for entry in self.entries:
            family, key = [x.strip("/") for x in entry.rsplit("/", 1)]
            db_result = await self.asterisk_conn.agi.database_del(family, key)
            self.log.info(
                f"[{self.channel.channel_uniqueid}] Delete family,key:{entry} result {db_result.result}"
            )

        await self._update_node(o_connection=self.o_connection)
