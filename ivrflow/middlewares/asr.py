from asyncio import gather
from time import time
from typing import Dict, Tuple

from aiohttp import ClientTimeout, ContentTypeError, FormData
from sqids import Sqids

from ..channel import Channel
from ..models import ASRMiddleware as ASRMiddlewareModel
from ..nodes import Base

sqids = Sqids()


class ASRMiddleware(Base):
    def __init__(
        self,
        asr_middleware_content: ASRMiddlewareModel,
        channel: Channel,
        default_variables: Dict,
    ) -> None:
        Base.__init__(self, channel=channel, default_variables=default_variables)
        self.log = self.log.getChild(asr_middleware_content.id)
        self.content: ASRMiddlewareModel = asr_middleware_content

    @property
    def method(self) -> str:
        return self.content.method

    @property
    def url(self) -> str:
        return self.render_data(self.content.url)

    @property
    def cookies(self) -> Dict:
        return self.render_data(self.content.cookies)

    @property
    def headers(self) -> Dict:
        return self.render_data(self.content.headers)

    @property
    def basic_auth(self) -> Dict:
        return self.render_data(self.content.basic_auth)

    @property
    def query_params(self) -> Dict:
        return self.render_data(self.content.query_params)

    @property
    def data(self) -> Dict:
        return self.render_data(self.content.data)

    @property
    def json(self) -> Dict:
        return self.render_data(self.content.json)

    async def run(self, extended_data: Dict):
        record_suffix = sqids.encode([int(time())])
        record_filename = f"{self.channel.channel_uniqueid}_{record_suffix}"

        if extended_data.get("prompt_file"):
            await self.asterisk_conn.agi.stream_file(extended_data.get("prompt_file"))

        result = await self.asterisk_conn.agi.record_file(
            filename=record_filename,
            audio_format=self.content.record_format,
            escape_digits=self.content.escape_digits,
            timeout=self.content.timeout,
            silence=self.content.silence,
        )

        file_name_recorded = f"{record_filename}.{self.content.record_format}"
        await self.channel.set_variable("record_path_variable", file_name_recorded)

        await self.channel.set_variable("asr_file_path", record_filename)
        if extended_data.get("progress_sound"):
            (_, result) = await gather(
                self.asterisk_conn.agi.stream_file(extended_data.get("progress_sound")),
                self.http_request(),
            )
        else:
            result = await self.http_request()

        return result

    async def http_request(self) -> Tuple[int, str]:
        """Recognize the text and return the status code and the text."""

        request_body = {}

        if self.query_params:
            request_body["params"] = self.query_params

        if self.headers:
            request_body["headers"] = self.headers

        if self.data:
            form_data = FormData()
            for key, value in self.data.items():
                form_data.add_field(name=key, value=value)
            request_body["data"] = form_data

        if self.json:
            request_body["json"] = self.json

        try:
            timeout = ClientTimeout(total=self.config["ivrflow.timeouts.middlewares"])
            response = await self.session.request(
                self.method,
                self.url,
                timeout=timeout,
                **request_body,
            )
        except Exception as e:
            self.log.exception(f"Error in middleware: {e}")
            return

        variables = {}

        if self.cookies:
            for cookie in self.cookies:
                variables[cookie] = response.cookies.output(cookie)

        self.log.debug(
            f"middleware: {self.id}  type: {self.type} method: {self.method} "
            f"url: {self.url} status: {response.status}"
        )

        try:
            response_data = await response.json()
        except ContentTypeError:
            response_data = {}

        await self.channel.set_variable(self.id, response_data)

        return response_data
