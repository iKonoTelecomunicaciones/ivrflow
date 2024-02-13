from typing import Dict

from ..channel import Channel, ChannelState
from ..models import SetVariable as SetVariableModel
from .base import Base


class SetVariable(Base):
    def __init__(
        self, default_variables: Dict, set_variable_content: SetVariableModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(set_variable_content.id)
        self.content: SetVariableModel = set_variable_content

    @property
    def variables(self):
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
        self.log.info(
            f"Channel {self.channel.channel_uniqueid} enters set_variable node {self.id}"
        )

        key_str = f"ARRAY({'|'.join(self.variables.keys())})"
        value_str = f"{'|'.join(self.variables.values())}"

        await self.asterisk_conn.agi.set_variable(key_str, value_str)

        await self._update_node()
