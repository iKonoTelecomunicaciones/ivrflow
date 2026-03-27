from typing import Dict

from ..channel import Channel, ChannelState
from ..models import SetMusic as SetMusicModel
from .base import Base


class SetMusic(Base):
    def __init__(
        self, default_variables: Dict, set_music_content: SetMusicModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(set_music_content.id)
        self.content: SetMusicModel = set_music_content

    @property
    def type(self) -> int:
        return self.render_data(data=self.content.type)

    @property
    def music_class(self) -> int:
        return self.render_data(data=self.content.music_class)

    @property
    def toggle(self) -> int:
        return self.render_data(data=self.content.toggle)

    @property
    def o_connection(self) -> str:
        return self.get_o_connection()

    async def run(self):
        self.log.info(f"[{self.channel.channel_uniqueid}] Entering set_music node {self.id}")

        await self.asterisk_conn.agi.set_music(toggle=self.toggle, music=self.music_class)

        await self._update_node(o_connection=self.o_connection)
