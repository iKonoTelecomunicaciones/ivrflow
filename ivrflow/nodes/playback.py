from typing import TYPE_CHECKING, Dict

from ..channel import Channel
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
    def escape_digits(self) -> str:
        return self.render_data(data=self.content.escape_digits)

    @property
    def o_connection(self) -> str:
        return self.get_o_connection()

    @property
    def sample_offset(self) -> int:
        return self.render_data(data=self.content.sample_offset)

    async def run(self) -> None:
        self.log.info(f"[{self.channel.channel_uniqueid}] Entering playback node {self.id}")

        if self.middleware:
            middleware_extended_data = self.render_data(
                self.content.middleware.get(self.middleware.id)
            )
            await self.middleware.run(middleware_extended_data)
        sound_path = self.file
        escape_digits = self.escape_digits
        sample_offset = self.sample_offset

        self.log.debug(
            f"[{self.channel.channel_uniqueid}] Playing file ({sound_path}) "
            f"with escape digits ({escape_digits}) and sample offset ({sample_offset}) on channel"
        )
        await self.asterisk_conn.agi.stream_file(
            filename=sound_path, escape_digits=escape_digits, sample_offset=sample_offset
        )

        await self._update_node(o_connection=self.o_connection)
