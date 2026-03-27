from typing import Dict

from ..channel import Channel, ChannelState
from ..models import Verbose as VerboseModel
from .base import Base


class Verbose(Base):
    def __init__(
        self, default_variables: Dict, verbose_content: VerboseModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(verbose_content.id)
        self.content: VerboseModel = verbose_content

    @property
    def message(self):
        return self.render_data(data=self.content.message)

    @property
    def level(self):
        return self.render_data(data=self.content.level)

    @property
    def o_connection(self) -> str:
        return self.get_o_connection()

    async def run(self):
        self.log.info(f"[{self.channel.channel_uniqueid}] Entering verbose node {self.id}")

        await self.asterisk_conn.agi.verbose(
            message=self.message,
            level=self.level,
        )
        await self._update_node(o_connection=self.o_connection)
