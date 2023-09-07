from typing import TYPE_CHECKING, Dict

from ..channel import Channel
from ..models import GetData as GetDataModel
from .switch import Switch

if TYPE_CHECKING:
    from ..middlewares import TTSMiddleware


class GetData(Switch):
    middleware: "TTSMiddleware" = None

    def __init__(self, get_data_content: GetDataModel, channel: Channel, default_variables: Dict):
        super().__init__(get_data_content, channel, default_variables)
        self.content: GetDataModel = get_data_content

    @property
    def file(self) -> str:
        return self.render_data(data=self.content.file)

    @property
    def text(self) -> str:
        return self.render_data(data=self.content.text)

    @property
    def timeout(self) -> int:
        return self.render_data(data=self.content.timeout)

    @property
    def max_digits(self) -> int:
        return self.render_data(data=self.content.max_digits)

    async def run(self):
        self.log.info(f"Channel {self.channel.channel_uniqueid} enters input node {self.id}")

        sound_path = self.file
        if self.middleware and self.text:
            await self.channel.set_variable("tts_text", self.text)
            await self.middleware.run()
            sound_path = self.middleware.sound_path

        variable = await self.asterisk_conn.agi.get_data(
            filename=sound_path,
            timeout=self.timeout,
            max_digits=self.max_digits,
        )

        await self.channel.set_variable(self.content.variable, variable.result)

        await super().run()
