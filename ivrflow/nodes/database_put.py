from typing import Dict

from ..channel import Channel, ChannelState
from ..models import DatabasePut as DatabasePutModel
from .base import Base


class DatabasePut(Base):
    def __init__(
        self, default_variables: Dict, database_put_content: DatabasePutModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(database_put_content.id)
        self.content: DatabasePutModel = database_put_content

    @property
    def entries(self) -> dict:
        return self.render_data(data=self.content.entries)

    @property
    def o_connection(self) -> str:
        return self.render_data(self.content.get("o_connection", ""))

    async def _update_node(self):
        await self.channel.update_ivr(
            node_id=self.o_connection,
            state=ChannelState.END if not self.o_connection else None,
        )

    async def run(self):
        for entry, variable in self.entries.items():
            family, key = [x.strip("/") for x in entry.rsplit("/", 1)]
            db_result = await self.asterisk_conn.agi.database_put(family, key, variable)
            self.log.info(
                f"node database_put send family,key:{entry} with value:{variable} result {db_result.result}"
            )

        await self._update_node()
