from typing import Dict, List

from ..channel import Channel, ChannelState
from ..models import SetVars as SetVarsModel
from .base import Base


class SetVars(Base):
    def __init__(
        self, default_variables: Dict, set_vars_content: SetVarsModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(set_vars_content.id)
        self.content: SetVarsModel = set_vars_content

    @property
    def variables(self) -> SetVarsModel:
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
        """This function runs the set_var node."""
        self.log.info(f"[{self.channel.channel_uniqueid}] Entering set_vars node {self.id}")
        if not self.variables:
            self.log.warning(
                f"[{self.channel.channel_uniqueid}] The variables in {self.id} have not been set because they are empty"
            )
            return

        try:
            # Set variables
            set_vars: Dict = self.variables.get("set")
            if set_vars:
                await self.channel.set_variables(variables=set_vars)

            # Unset variables
            unset_vars: List = self.variables.get("unset")
            if unset_vars:
                await self.channel.del_variables(variables=unset_vars)
        except ValueError as e:
            self.log.warning(f"[{self.channel.channel_uniqueid}] Error: {e}")

        await self._update_node()
