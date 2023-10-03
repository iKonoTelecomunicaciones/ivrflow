from typing import Dict

from ..channel import Channel, ChannelState
from ..models import GetVariable as GetVariableModel
from .base import Base


class GetVariable(Base):
    def __init__(
        self, default_variables: Dict, get_variable_content: GetVariableModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(get_variable_content.id)
        self.content: GetVariableModel = get_variable_content

    @property
    def variable(self) -> str:
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
            f"Channel {self.channel.channel_uniqueid} enters get_variable node {self.id}"
        )

        await self.asterisk_conn.agi.get_variable(self.variable)

        await self._update_node()
