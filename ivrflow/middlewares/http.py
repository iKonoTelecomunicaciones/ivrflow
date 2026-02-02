from typing import Dict, Tuple

from aiohttp import ClientTimeout, ContentTypeError
from mautrix.util.config import RecursiveDict
from ruamel.yaml.comments import CommentedMap

from ..channel import Channel
from ..models import HTTPMiddleware as HTTPMiddlewareModel
from ..nodes import Base


class HTTPMiddleware(Base):
    def __init__(
        self,
        http_middleware_content: HTTPMiddlewareModel,
        channel: Channel,
        default_variables: Dict,
    ) -> None:
        Base.__init__(self, channel=channel, default_variables=default_variables)
        self.log = self.log.getChild(http_middleware_content.id)
        self.content: HTTPMiddleware = http_middleware_content

    @property
    def url(self) -> str:
        return self.render_data(self.content.url)

    @property
    def token_type(self) -> str:
        return self.render_data(self.content.token_type)

    @property
    def auth(self) -> Dict:
        return self.render_data(self.content.auth)

    @property
    def general(self) -> Dict:
        return self.render_data(self.content.general)

    @property
    def token_url(self) -> str:
        complete_url = f"{self.url}{self.auth.get('token_path')}"
        return self.render_data(complete_url)

    @property
    def attempts(self) -> int:
        return int(self.auth.get("attempts", 2))

    @property
    def middleware_variables(self) -> Dict:
        return self.render_data(self.auth.get("variables", {}))

    @property
    def method(self) -> Dict:
        return self.render_data(self.auth.get("method", ""))

    @property
    def cookies(self) -> Dict:
        return self.render_data(self.auth.get("cookies", {}))

    @property
    def headers(self) -> Dict:
        return self.render_data(self.auth.get("headers", {}))

    @property
    def query_params(self) -> Dict:
        return self.render_data(self.auth.get("query_params", {}))

    @property
    def data(self) -> Dict:
        return self.render_data(self.auth.get("data", {}))

    @property
    def json(self) -> Dict:
        return self.render_data(self.auth.get("json", {}))

    @property
    def basic_auth(self) -> Dict:
        return self.render_data(self.auth.get("basic_auth", {}))

    async def auth_request(self) -> Tuple[int, str]:
        """Make the auth request to refresh api token

        Parameters
        ----------
        session : ClientSession
            ClientSession

        Returns
        -------
            The status code and the response text.

        """

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
                self.method, self.token_url, timeout=timeout, **request_body
            )
        except Exception as e:
            self.log.exception(f"[{self.channel.channel_uniqueid}] Error in middleware: {e}")
            return

        variables = {}

        if self.cookies:
            for cookie in self.cookies:
                variables[cookie] = response.cookies.output(cookie)

        self.log.debug(
            f"[{self.channel.channel_uniqueid}] middleware: {self.id}  type: {self.type} method: {self.method} "
            f"url: {self.token_url} status: {response.status}"
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
