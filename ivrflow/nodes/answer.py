from typing import Dict

from ..channel import Channel, ChannelState
from ..models import Answer as AnswerModel
from .base import Base


class Answer(Base):
    def __init__(
        self, default_variables: Dict, answer_content: AnswerModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(answer_content.id)
        self.content: AnswerModel = answer_content

    @property
    def o_connection(self) -> str:
        return self.render_data(self.content.get("o_connection", ""))

    async def run(self):
        self.log.info(f"[{self.channel.channel_uniqueid}] Entering answer node {self.id}")

        result = await self.asterisk_conn.agi.answer()
        self.log.info(
            f"[{self.channel.channel_uniqueid}] Answer node {self.id} result: {result.result}"
        )

        await self._update_node(o_connection=self.o_connection)
