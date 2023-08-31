from typing import Dict

from ..channel import Channel
from ..repository import GetData as GetDataModel
from .switch import Switch


class GetData(Switch):
    def __init__(self, get_data_content: GetDataModel, channel: Channel, default_variables: Dict):
        super().__init__(get_data_content, channel, default_variables)
        self.content: GetDataModel = get_data_content

    @property
    def file(self) -> str:
        return self.render_data(data=self.content.file)

    @property
    def timeout(self) -> int:
        return self.render_data(data=self.content.timeout)

    @property
    def max_digits(self) -> int:
        return self.render_data(data=self.content.max_digits)

    async def run(self):
        self.log.info(f"Channel {self.channel.channel_uniqueid} enters input node {self.id}")

        variable = await self.asterisk_conn.agi.get_data(
            filename=self.file,
            timeout=self.timeout,
            max_digits=self.max_digits,
        )

        await self.channel.set_variable(self.content.variable, variable.result)

        await super().run()
