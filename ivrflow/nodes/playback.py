from typing import Dict

from ..repository import Playback as PlaybackModel
from .base import Base


class Playback(Base):
    def __init__(
        self, default_variables: Dict, playback_content: PlaybackModel
    ) -> None:
        super().__init__(default_variables)
        self.content: PlaybackModel = playback_content

    @property
    def file(self) -> str:
        return self.render_data(data=self.content.file)

    async def run(self) -> None:
        self.log.info(
            f"Channel {self.asterisk_conn.headers['agi_channel']} enters message node {self.id}"
        )
        await self.asterisk_conn.agi.stream_file(self.file)
        await self.asterisk_conn.agi.verbose(
            "HelloView handler: {}.".format(self.asterisk_conn.rel_url.query)
        )
