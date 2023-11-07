from typing import Dict

from ..channel import Channel, ChannelState
from ..models import GotoOnExit as GotoOnExitModel
from .base import Base


class GotoOnExit(Base):
    def __init__(
        self,
        default_variables: Dict,
        goto_on_exit_content: GotoOnExitModel,
        channel: Channel,
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(goto_on_exit_content.id)
        self.content: GotoOnExitModel = goto_on_exit_content

    @property
    def context(self) -> dict:
        return self.render_data(data=self.content.context)

    @property
    def extension(self) -> dict:
        return self.render_data(data=self.content.extension)

    @property
    def priority(self) -> dict:
        return self.render_data(data=self.content.priority)

    async def _update_node(self):
        await self.channel.update_ivr(
            node_id=None,
            state=ChannelState.END,
        )

    async def run(self):
        self.log.info(
            f"Channel {self.channel.channel_uniqueid} enters goto_on_exit node {self.id}"
        )

        await self.asterisk_conn.agi.goto_on_exit(
            context=self.context, extension=self.extension, priority=self.priority
        )

        await self._update_node()
