from typing import Dict

from ..channel import Channel
from ..db.channel import ChannelState
from ..models import NoOp as NoOpModel
from .base import Base


class NoOp(Base):

    def __init__(
        self, default_variables: Dict, no_op_content: NoOpModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(no_op_content.id)
        self.content: NoOpModel = no_op_content

    @property
    def text(self) -> str:
        return self.render_data(data=self.content.text)

    @property
    def o_connection(self) -> str:
        return self.get_o_connection()

    async def _update_node(self):
        await self.channel.update_ivr(
            node_id=self.o_connection,
            state=ChannelState.END if not self.o_connection else None,
        )

    async def run(self) -> None:
        self.log.info(f"[{self.channel.channel_uniqueid}] Entering no_op node {self.id}")

        if self.text:
            self.log.debug(f"[{self.channel.channel_uniqueid}] log message: {self.text}")

        if not self.text or self.text == ".":
            self.log.debug(
                f"[{self.channel.channel_uniqueid}] "
                f"all variables: {repr(self.channel._variables | self.default_variables)}"
            )

        await self._update_node()
