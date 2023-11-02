from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

from ..channel import Channel
from ..models import GetData as GetDataModel
from ..types import MiddlewareType
from .switch import Switch

if TYPE_CHECKING:
    from ..middlewares import ASRMiddleware, TTSMiddleware


class GetData(Switch):
    middleware: TTSMiddleware | ASRMiddleware | List[ASRMiddleware, TTSMiddleware] = None

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
        if isinstance(self.middleware, list):
            for md in self.middleware:
                middleware_type = MiddlewareType(md.type) if md else None
                if middleware_type == MiddlewareType.tts and self.text:
                    await self.channel.set_variable("tts_text", self.text)
                    await md.run()
                    sound_path = md.sound_path
                elif middleware_type == MiddlewareType.asr:
                    result = await md.run(sound_path)
        elif self.middleware:
            middleware_type = MiddlewareType(self.middleware.type)
            if middleware_type == MiddlewareType.tts and self.text:
                await self.channel.set_variable("tts_text", self.text)
                await self.middleware.run()

                variable = await self.asterisk_conn.agi.get_data(
                    filename=self.middleware.sound_path,
                    timeout=self.timeout,
                    max_digits=self.max_digits,
                )
                result = variable.result
            elif middleware_type == MiddlewareType.asr:
                result = await self.middleware.run(sound_path)
        else:
            variable = await self.asterisk_conn.agi.get_data(
                filename=sound_path,
                timeout=self.timeout,
                max_digits=self.max_digits,
            )
            result = variable.result

        await self.channel.set_variable(self.content.variable, result)

        await super().run()
