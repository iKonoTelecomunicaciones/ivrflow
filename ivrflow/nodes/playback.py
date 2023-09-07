from typing import TYPE_CHECKING, Dict

from ..channel import Channel
from ..db.channel import ChannelState
from ..models import Playback as PlaybackModel
from .base import Base

if TYPE_CHECKING:
    from ..middlewares import TTSMiddleware


class Playback(Base):
    middleware: "TTSMiddleware" = None

    def __init__(
        self, default_variables: Dict, playback_content: PlaybackModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(playback_content.id)
        self.content: PlaybackModel = playback_content

    @property
    def file(self) -> str:
        return self.render_data(data=self.content.file)

    @property
    def text(self) -> str:
        return self.render_data(data=self.content.text)

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

        sound_path = self.file
        if self.middleware and self.text:
            await self.channel.set_variable("tts_text", self.text)
            await self.middleware.run()
            sound_path = self.middleware.sound_path

        await self.asterisk_conn.agi.stream_file(
            filename=sound_path, escape_digits=self.escape_digits, sample_offset=self.sample_offset
        )

        await self._update_node()
