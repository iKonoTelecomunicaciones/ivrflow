from time import time
from typing import TYPE_CHECKING, Dict, Union

from sqids import Sqids

from ..channel import Channel
from ..models import GetData as GetDataModel
from ..types import MiddlewareType
from .switch import Switch

if TYPE_CHECKING:
    from ..middlewares import ASRMiddleware, TTSMiddleware

sqids = Sqids()


class GetData(Switch):
    middleware: Union["TTSMiddleware", "ASRMiddleware"] = None

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

        middleware_type = MiddlewareType(self.middleware.type) if self.middleware else None

        sound_path = self.file
        if middleware_type == MiddlewareType.tts and self.text:
            await self.channel.set_variable("tts_text", self.text)
            await self.middleware.run()
            sound_path = self.middleware.sound_path
            await self.channel.set_variable("tts_sound_path", sound_path)

        if middleware_type == MiddlewareType.asr:
            record_suffix = sqids.encode([int(time())])
            record_filename, record_format = (
                f"{self.channel.channel_uniqueid}_{record_suffix}",
                "wav",
            )

            if sound_path:
                await self.asterisk_conn.agi.stream_file(sound_path)
            result = await self.asterisk_conn.agi.record_file(
                filename=record_filename,
                audio_format=record_format,
                escape_digits="#",
                timeout=20000,
                silence=2000,
            )
            await self.channel.set_variable("asr", "{}")
            await self.channel.set_variable("asr_file_path", f"{record_filename}.{record_format}")
            await self.middleware.run()
            result = self.middleware.text
            await self.channel.set_variable("asr_text", result)

        else:
            variable = await self.asterisk_conn.agi.get_data(
                filename=sound_path,
                timeout=self.timeout,
                max_digits=self.max_digits,
            )
            result = variable.result

        await self.channel.set_variable(self.content.variable, result)

        await super().run()
