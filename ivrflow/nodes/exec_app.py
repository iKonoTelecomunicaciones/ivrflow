from typing import Dict

from ..channel import Channel, ChannelState
from ..models import Exec_App as Exec_AppModel
from .base import Base


class Exec_App(Base):
    def __init__(
        self, default_variables: Dict, exec_app_content: Exec_AppModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(exec_app_content.id)
        self.content: Exec_AppModel = exec_app_content

    @property
    def application(self):
        return self.render_data(data=self.content.application)

    @property
    def options(self):
        return self.render_data(data=self.content.options)

    @property
    def o_connection(self) -> str:
        return self.render_data(self.content.get("o_connection", ""))

    async def _update_node(self):
        await self.channel.update_ivr(
            node_id=self.o_connection,
            state=ChannelState.END if not self.o_connection else None,
        )

    async def run(self):
        self.log.info(f"Channel {self.channel.channel_uniqueid} enters exec_app node {self.id}")
        self.log.info(
            f"Setting Exec_App '{self.application}' and '{self.options}' to channel: {self.channel.channel_uniqueid}"
        )

        await self.asterisk_conn.agi.exec_app(
            application=self.application,
            options=self.options,
        )
        await self._update_node()
