from typing import TYPE_CHECKING, Dict, Union

from ..channel import Channel
from ..models import GetData as GetDataModel
from ..types import MiddlewareType
from .switch import Switch

if TYPE_CHECKING:
    from ..middlewares import ASRMiddleware, TTSMiddleware


class GetData(Switch):
    middlewares: Union["TTSMiddleware", "ASRMiddleware"] = []

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
        self.log.info(f"[{self.channel.channel_uniqueid}] Entering get_data node {self.id}")

        middlewares_sorted = {
            MiddlewareType(middleware.type): middleware for middleware in self.middlewares
        }

        tts_middleware: TTSMiddleware = middlewares_sorted.get(MiddlewareType.tts)
        if tts_middleware:
            self.log.info(
                f"[{self.channel.channel_uniqueid}] Running TTS middleware {tts_middleware.id}"
            )
            middleware_extended_data = self.render_data(
                self.content.middlewares.get(tts_middleware.id)
            )
            await tts_middleware.run(extended_data=middleware_extended_data)

        asr_middleware: ASRMiddleware = middlewares_sorted.get(MiddlewareType.asr)
        if asr_middleware:
            self.log.info(
                f"[{self.channel.channel_uniqueid}] Running ASR middleware {asr_middleware.id}"
            )
            middleware_extended_data = self.render_data(
                self.content.middlewares.get(asr_middleware.id)
            )
            await asr_middleware.run(middleware_extended_data)
        else:
            response = await self.asterisk_conn.agi.get_data(
                filename=self.file,
                timeout=self.timeout,
                max_digits=self.max_digits,
            )
            value, timeout = response.result, response.info == "(timeout)"
            result = "timeout" if timeout else value
            await self.channel.set_variable(self.content.dtmf_input, result)

        await super().run()
