from typing import Dict, Tuple

from aiohttp import ClientTimeout, ContentTypeError

from ..channel import Channel
from ..models import LLMMiddleware as LLMMiddlewareModel
from ..nodes import Base
from ..utils import Util


class LLMMiddleware(Base):
    def __init__(
        self,
        llm_middleware_content: LLMMiddlewareModel,
        channel: Channel,
        default_variables: Dict,
    ) -> None:
        Base.__init__(self, channel=channel, default_variables=default_variables)
        self.log = self.log.getChild(llm_middleware_content.id)
        self.content: LLMMiddlewareModel = llm_middleware_content

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
    def cookies(self) -> Dict:
        return self.render_data(self.content.cookies)

    @property
    def headers(self) -> Dict:
        return self.render_data(self.content.headers)

    @property
    def basic_auth(self) -> Dict:
        return self.render_data(self.content.basic_auth)

    @property
    def json(self) -> Dict:
        return self.render_data(self.content.json)

    @property
    def query_params(self) -> Dict:
        return self.render_data(self.content.query_params)

    async def run(self, extended_json: Dict) -> Tuple[int, str]:
        """Generate a text from a prompt and return the status code and the text."""
        self.log.info(f"[{self.channel.channel_uniqueid}] Running LLM middleware {self.id}")

        request_body = {}

        if _query_params := self.query_params:
            request_body["params"] = _query_params

        if _headers := self.headers:
            request_body["headers"] = _headers

        if _json := self.json:
            request_body["json"] = _json | extended_json

        try:
            timeout = ClientTimeout(total=self.config["ivrflow.timeouts.middlewares"])
            response = await self.session.request(
                self.method, self.url, timeout=timeout, **request_body
            )
        except Exception as e:
            self.log.exception(f"[{self.channel.channel_uniqueid}] Error in middleware: {e}")
            return

        variables = {}

        if _cookies := self.cookies:
            for cookie in _cookies:
                variables[cookie] = response.cookies.output(cookie)

        self.log.debug(
            f"[{self.channel.channel_uniqueid}] middleware: {self.id}  type: {self.type} method: {self.method} "
            f"url: {self.url} status: {response.status}"
        )

        try:
            response_data = await response.json()
        except ContentTypeError:
            response_data = {}

        _variables = self.middleware_variables
        if isinstance(response_data, (dict, list, str)) and _variables:
            for variable in _variables:
                if isinstance(response_data, str):
                    try:
                        variables[variable] = self.render_data(response_data)
                    except KeyError:
                        pass
                    break
                else:
                    default_value = None
                    jq_result: dict = Util.jq_compile(_variables[variable], response_data)
                    if jq_result.get("status") != 200:
                        self.log.error(
                            f"[{self.channel.channel_uniqueid}] Error parsing '{_variables[variable]}' with jq "
                            f"on variable '{variable}'. Set to default value ({default_value}). "
                            f"Error message: {jq_result.get('error')}, Status: {jq_result.get('status')}"
                        )
                    data_match = jq_result.get("result")

                    try:
                        data_match = default_value if not data_match else data_match
                        variables[variable] = (
                            data_match if not data_match or len(data_match) > 1 else data_match[0]
                        )
                    except KeyError:
                        pass
        if variables:
            await self.channel.set_variable(self.id, variables)

        return response.status, await response.text()
