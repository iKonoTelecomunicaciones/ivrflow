from typing import TYPE_CHECKING, Dict

from aiohttp import BasicAuth, ClientTimeout, ContentTypeError
from mautrix.util.config import RecursiveDict
from ruamel.yaml.comments import CommentedMap

from ..channel import Channel
from ..db.channel import ChannelState
from ..models import HTTPRequest as HTTPRequestModel
from .switch import Switch

if TYPE_CHECKING:
    from ..middlewares import HTTPMiddleware


class HTTPRequest(Switch):
    HTTP_ATTEMPTS: Dict = {}

    middleware: "HTTPMiddleware" = None

    def __init__(
        self, http_request_content: HTTPRequestModel, channel: Channel, default_variables: Dict
    ) -> None:
        Switch.__init__(
            self, http_request_content, channel=channel, default_variables=default_variables
        )
        self.log = self.log.getChild(http_request_content.id)
        self.content: HTTPRequestModel = http_request_content

    @property
    def method(self) -> str:
        return self.content.method

    @property
    def url(self) -> str:
        return self.render_data(self.content.url)

    @property
    def http_variables(self) -> Dict:
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
    def query_params(self) -> Dict:
        return self.render_data(self.content.query_params)

    @property
    def data(self) -> Dict:
        return self.render_data(self.content.data)

    @property
    def json(self) -> Dict:
        return self.render_data(self.content.json)

    @property
    def context_params(self) -> Dict[str, str]:
        return {"channel_uniqueid": self.channel.channel_uniqueid}

    def prepare_request(self) -> Dict:
        request_body = {}

        if self.query_params:
            request_body["params"] = self.query_params

        if self.basic_auth:
            request_body["auth"] = BasicAuth(
                login=self.basic_auth["login"],
                password=self.basic_auth["password"],
            )

        if self.headers:
            request_body["headers"] = self.headers

        if self.data:
            request_body["data"] = self.data

        if self.json:
            request_body["json"] = self.json

        return request_body

    async def make_request(self):
        """It makes a request to the URL specified in the node,
        and then it does some stuff with the response

        Returns
        -------
            The status code and the response text.
        """

        self.log.debug(
            f"Channel {self.channel.channel_uniqueid} enters http_request node {self.id}"
        )

        request_body = self.prepare_request()

        if self.middleware:
            self.middleware.channel = self.channel
            request_params_ctx = self.context_params
            request_params_ctx.update({"middleware": self.middleware})
        else:
            request_params_ctx = {}

        try:
            timeout = ClientTimeout(total=self.config["ivrflow.timeouts.http_request"])
            response = await self.session.request(
                self.method,
                self.url,
                **request_body,
                trace_request_ctx=request_params_ctx,
                timeout=timeout,
            )
        except Exception as e:
            self.log.exception(f"Error in http_request node: {e}")
            o_connection = await self.get_case_by_id(id=500)
            await self.channel.update_ivr(node_id=o_connection, state=None)
            return 500, e

        self.log.debug(
            f"node: {self.id} method: {self.method} url: {self.url} status: {response.status}"
        )

        if response.status == 401:
            if not self.middleware:
                if self.cases:
                    o_connection = await self.get_case_by_id(id=response.status)

                if o_connection:
                    await self.channel.update_ivr(
                        node_id=o_connection, state=ChannelState.END if not self.cases else None
                    )
            return response.status, None

        variables = {}
        o_connection = None

        if self.cookies:
            for cookie in self.cookies:
                variables[cookie] = response.cookies.output(cookie)

        try:
            response_data = await response.json()
        except ContentTypeError:
            response_data = {}

        if isinstance(response_data, dict):
            # Tulir and its magic since time immemorial
            serialized_data = RecursiveDict(CommentedMap(**response_data))
            if self.http_variables:
                for variable in self.http_variables:
                    try:
                        variables[variable] = self.render_data(
                            serialized_data[self.http_variables[variable]]
                        )
                    except KeyError:
                        pass
        elif isinstance(response_data, str):
            if self.http_variables:
                for variable in self.http_variables:
                    try:
                        variables[variable] = self.render_data(response_data)
                    except KeyError:
                        pass

                    break

        if self.cases:
            o_connection = await self.get_case_by_id(id=response.status)

        if o_connection:
            await self.channel.update_ivr(
                node_id=o_connection, state=ChannelState.END if not self.cases else None
            )

        if variables:
            await self.channel.set_variables(variables=variables)

        return response.status, await response.text()

    async def run_middleware(self, status: int):
        """This function check athentication attempts to avoid an infinite try_athentication cicle.

        Parameters
        ----------
        status : int
            Http status of the request.

        """

        if status in [200, 201]:
            self.HTTP_ATTEMPTS.update(
                {self.channel.channel_uniqueid: {"last_http_node": None, "attempts_count": 0}}
            )
            return

        if (
            self.HTTP_ATTEMPTS.get(self.channel.channel_uniqueid)
            and self.HTTP_ATTEMPTS[self.channel.channel_uniqueid]["last_http_node"] == self.id
            and self.HTTP_ATTEMPTS[self.channel.channel_uniqueid]["attempts_count"]
            >= self.middleware.attempts
        ):
            self.log.debug("Attempts limit reached, o_connection set as `default`")
            self.HTTP_ATTEMPTS.update(
                {self.channel.channel_uniqueid: {"last_http_node": None, "attempts_count": 0}}
            )
            await self.channel.update_ivr(await self.get_case_by_id("default"), None)

        if status == 401:
            self.HTTP_ATTEMPTS.update(
                {
                    self.channel.channel_uniqueid: {
                        "last_http_node": self.id,
                        "attempts_count": self.HTTP_ATTEMPTS.get(
                            self.channel.channel_uniqueid, {}
                        ).get("attempts_count")
                        + 1
                        if self.HTTP_ATTEMPTS.get(self.channel.channel_uniqueid)
                        else 1,
                    }
                }
            )
            self.log.debug(
                "HTTP auth attempt "
                f"{self.HTTP_ATTEMPTS[self.channel.channel_uniqueid]['attempts_count']}, "
                "trying again ..."
            )

    async def run(self):
        """It makes a request to the URL specified in the node's configuration,
        and then runs the middleware
        """
        try:
            status, response = await self.make_request()
            self.log.info(f"http_request node {self.id} had a status of {status}")
        except Exception as e:
            self.log.exception(e)

        if self.middleware:
            await self.run_middleware(status=status)
