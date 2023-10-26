from typing import Dict

from ..channel import Channel, ChannelState
from ..models import DatabaseGet as DatabaseGetModel
from .base import Base


class DatabaseGet(Base):
    def __init__(
        self, default_variables: Dict, database_get_content: DatabaseGetModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(database_get_content.id)
        self.content: DatabaseGetModel = database_get_content

    @property
    def family(self):
        return self.render_data(data=self.content.family)

    @property
    def key(self):
        return self.render_data(data=self.content.key)

    @property
    def variable(self):
        return self.render_data(data=self.content.variable)

    @property
    def o_connection(self) -> str:
        return self.render_data(self.content.get("o_connection", ""))

    async def _update_node(self):
        await self.channel.update_ivr(
            node_id=self.o_connection,
            state=ChannelState.END if not self.o_connection else None,
        )

    async def run(self):
        self.log.info(
            f"Channel {self.channel.channel_uniqueid} enters database_get node {self.id}"
        )
        self.log.info(
            f"Setting database_get Family='{self.family}' and Key='{self.key}' to channel: {self.channel.channel_uniqueid}"
        )

        database_get_info = await self.asterisk_conn.agi.database_get(
            family=self.family,
            key=self.key,
        )
        value = database_get_info.data.get("data")

        self.log.info(f" ### database_get_info'{database_get_info}' and '{value}'")

        await self.channel.set_variable(self.content.variable, value)

        await self._update_node()
