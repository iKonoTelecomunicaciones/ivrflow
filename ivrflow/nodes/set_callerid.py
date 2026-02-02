from typing import Dict

from ..channel import Channel, ChannelState
from ..models import SetCallerID as SetCallerIDModel
from .base import Base


class SetCallerID(Base):
    def __init__(
        self, default_variables: Dict, set_callerid_content: SetCallerIDModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(set_callerid_content.id)
        self.content: SetCallerIDModel = set_callerid_content

    @property
    def number(self):
        return self.render_data(data=self.content.number)

    @property
    def o_connection(self) -> str:
        return self.get_o_connection()

    async def _update_node(self):
        await self.channel.update_ivr(
            node_id=self.o_connection,
            state=ChannelState.END if not self.o_connection else None,
        )

    async def run(self):
        self.log.info(f"[{self.channel.channel_uniqueid}] Entering set_callerid node {self.id}")
        self.log.info(f"[{self.channel.channel_uniqueid}] Setting CallerID '{self.number}'")

        await self.asterisk_conn.agi.set_callerid(
            number=self.number,
        )
        await self._update_node()
