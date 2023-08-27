from typing import Dict

from ..channel import Channel
from ..db.channel import ChannelState
from ..repository import Playback as PlaybackModel
from .base import Base


class Playback(Base):
    def __init__(
        self, default_variables: Dict, playback_content: PlaybackModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.content: PlaybackModel = playback_content

    @property
    def file(self) -> str:
        return self.render_data(data=self.content.file)

    @property
    def escape_digits(self) -> str:
        return self.render_data(data=self.content.escape_digits)

    @property
    def o_connection(self) -> str:
        return self.render_data(self.content.get("o_connection", ""))

    @property
    def sample_offset(self) -> int:
        return self.render_data(data=self.content.sample_offset)

    async def _update_node(self):
        await self.channel.update_ivr(
            node_id=self.o_connection,
            state=ChannelState.END if not self.o_connection else None,
        )

    async def run(self) -> None:
        self.log.info(f"Channel {self.channel.channel_uniqueid} enters message node {self.id}")
        await self.asterisk_conn.agi.stream_file(
            filename=self.file, escape_digits=self.escape_digits, sample_offset=self.sample_offset
        )

        await self._update_node()
