from typing import Dict, Tuple

from aiohttp import ClientTimeout, ContentTypeError
from mautrix.util.config import RecursiveDict
from ruamel.yaml.comments import CommentedMap

from ..channel import Channel
from ..models import ASRMiddleware as ASRMiddlewareModel
from ..nodes import Base


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
    def middleware_variables(self) -> Dict:
        return self.render_data(self.content.variables)

    @property
    def text(self) -> str:
        return self.render_data(self.content.text)

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

    async def run(self) -> Tuple[int, str]:
        """Recognize the text and return the status code and the text."""

        request_body = {}

        if self.query_params:
            request_body["params"] = self.query_params

        if self.headers:
            request_body["headers"] = self.headers

        if self.data:
            request_body["data"] = self.data

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

        if isinstance(response_data, dict):
            # Tulir and its magic since time immemorial
            serialized_data = RecursiveDict(CommentedMap(**response_data))
            if self.middleware_variables:
                for variable in self.middleware_variables:
                    try:
                        variables[variable] = self.render_data(
                            serialized_data[self.middleware_variables[variable]]
                        )
                    except KeyError:
                        pass
        elif isinstance(response_data, str):
            if self.middleware_variables:
                for variable in self.middleware_variables:
                    try:
                        variables[variable] = self.render_data(response_data)
                    except KeyError:
                        pass

                    break

        if variables:
            await self.channel.set_variables(variables=variables)

        return response.status, await response.text()
