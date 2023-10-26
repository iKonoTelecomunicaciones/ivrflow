from typing import Dict

from ..channel import Channel, ChannelState
from ..models import Hangup as HangupModel
from .base import Base


class Hangup(Base):
    def __init__(
        self, default_variables: Dict, hangup_content: HangupModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(hangup_content.id)
        self.content: HangupModel = hangup_content

    @property
    def chan(self) -> int:
        return self.render_data(data=self.content.chan)

    async def _update_node(self):
        await self.channel.update_ivr(
            node_id=None,
            state=ChannelState.END,
        )

    async def run(self):
        self.log.info(f"Channel {self.channel.channel_uniqueid} enters record_file node {self.id}")
        await self.asterisk_conn.agi.hangup(channel=self.chan)
        await self._update_node()
