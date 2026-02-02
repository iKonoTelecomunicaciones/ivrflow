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
    def variables(self) -> dict:
        return self.render_data(data=self.content.variables)

    @property
    def o_connection(self) -> str:
        return self.get_o_connection()

    async def _update_node(self):
        await self.channel.update_ivr(
            node_id=self.o_connection,
            state=ChannelState.END if not self.o_connection else None,
        )

    async def run(self):
        self.log.info(f"[{self.channel.channel_uniqueid}] Entering database_get node {self.id}")
        for variable, entry in self.variables.items():
            family, key = [x.strip("/") for x in entry.rsplit("/", 1)]
            db_result = await self.asterisk_conn.agi.database_get(family, key)
            value = db_result.data.get("data")
            if value:
                self.log.info(
                    f"[{self.channel.channel_uniqueid}] Getting {variable}: {value} from {entry} database entry"
                )
                await self.channel.set_variable(variable, value)
            else:
                self.log.debug(
                    f"[{self.channel.channel_uniqueid}] No value found for variable {variable} in database entry {entry}"
                )

        await self._update_node()
