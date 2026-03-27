from typing import Dict

from ..channel import Channel, ChannelState
from ..models import ExecApp as ExecAppModel
from .base import Base


class ExecApp(Base):
    def __init__(
        self, default_variables: Dict, exec_app_content: ExecAppModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(exec_app_content.id)
        self.content: ExecAppModel = exec_app_content

    @property
    def application(self):
        return self.render_data(data=self.content.application)

    @property
    def options(self):
        return self.render_data(data=self.content.options)

    @property
    def o_connection(self) -> str:
        return self.get_o_connection()

    async def run(self):
        self.log.info(f"[{self.channel.channel_uniqueid}] Entering exec_app node {self.id}")
        self.log.info(
            f"[{self.channel.channel_uniqueid}] Setting ExecApp '{self.application}' and '{self.options}'"
        )

        await self.asterisk_conn.agi.exec_app(
            application=self.application,
            options=self.options,
        )
        await self._update_node(o_connection=self.o_connection)
