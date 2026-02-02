from typing import Dict

from ..channel import Channel, ChannelState
from ..models import Record as RecordModel
from .base import Base


class Record(Base):
    def __init__(
        self, default_variables: Dict, record_content: RecordModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(record_content.id)
        self.content: RecordModel = record_content

    @property
    def file(self):
        return self.render_data(data=self.content.file)

    @property
    def format(self):
        return self.render_data(data=self.content.format)

    @property
    def escape_digits(self):
        return self.render_data(data=self.content.escape_digits)

    @property
    def timeout(self):
        return self.render_data(data=self.content.timeout)

    @property
    def offset(self):
        return self.render_data(data=self.content.offset)

    @property
    def beep(self):
        return self.render_data(data=self.content.beep)

    @property
    def silence(self):
        return self.render_data(data=self.content.silence)

    @property
    def o_connection(self) -> str:
        return self.get_o_connection()

    async def _update_node(self):
        await self.channel.update_ivr(
            node_id=self.o_connection,
            state=ChannelState.END if not self.o_connection else None,
        )

    async def run(self):
        self.log.info(f"[{self.channel.channel_uniqueid}] Entering record_file node {self.id}")

        await self.asterisk_conn.agi.record_file(
            filename=self.file,
            audio_format=self.format,
            escape_digits=self.escape_digits,
            timeout=self.timeout,
            offset=self.offset,
            beep=self.beep,
            silence=self.silence,
        )
        await self._update_node()
