from typing import Dict

from ..channel import Channel, ChannelState
from ..models import GetFullVariable as GetFullVariableModel
from .base import Base


class GetFullVariable(Base):
    def __init__(
        self,
        default_variables: Dict,
        get_full_variable_content: GetFullVariableModel,
        channel: Channel,
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(get_full_variable_content.id)
        self.content: GetFullVariableModel = get_full_variable_content

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
        variables_to_set = {}

        for key, value in self.variables.items():
            result = await self.asterisk_conn.agi.get_full_variable(name=value)
            value = result.data.get("data")
            variables_to_set[key] = value

        await self.channel.set_variables(variables_to_set)

        self.log.info(
            f"Node {self.id}, variables to set: {variables_to_set}, to channel: {self.channel.channel_uniqueid}"
        )

        await self._update_node()
