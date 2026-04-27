from __future__ import annotations

from abc import abstractmethod
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from logging import Logger, getLogger
from typing import Any

from aiohttp import ClientSession

from ..channel import Channel
from ..config import Config
from ..db.channel import ChannelState
from ..utils import Util
from ..utils.flags import RenderFlags


@dataclass
class AGIContext:
    asterisk_conn: Any
    http_session: Any


_agi_ctx_var: ContextVar[AGIContext | None] = ContextVar("ivrflow_agi_ctx", default=None)


def convert_to_int(item: Any) -> dict | list | int:
    if isinstance(item, dict):
        for k, v in item.items():
            item[k] = convert_to_int(v)
        return item
    elif isinstance(item, list):
        return [convert_to_int(i) for i in item]
    elif isinstance(item, str) and item.strip().isdigit():
        return int(item.strip())
    else:
        return item


def safe_data_convertion(item: Any, _bool: bool = True, _int: bool = True) -> Any:
    if _bool:
        item = Util.convert_to_bool(item)

    if _int:
        item = convert_to_int(item)

    return item


class Base:
    log: Logger = getLogger("ivrflow.node")

    config: Config
    content: object
    channel: Channel

    def __init__(self, default_variables: dict, channel: Channel) -> None:
        self.default_variables = default_variables
        self.channel = channel

    @property
    def asterisk_conn(self) -> ClientSession | None:
        ctx = _agi_ctx_var.get()
        return ctx.asterisk_conn if ctx else None

    @property
    def session(self) -> ClientSession | None:
        ctx = _agi_ctx_var.get()
        return ctx.http_session if ctx else None

    @property
    def id(self) -> str:
        return self.content.id

    @property
    def type(self) -> str:
        return self.content.type

    @classmethod
    def init_cls(cls, config: Config) -> None:
        cls.config = config

    @abstractmethod
    async def run(self):
        pass

    def render_data(
        self,
        data: dict | list | str,
        flags: RenderFlags = RenderFlags.CONVERT_TO_TYPE
        | RenderFlags.LITERAL_EVAL
        | RenderFlags.REMOVE_QUOTES,
    ) -> dict | list | str:
        """It renders the data using the default variables and the room variables.

        Parameters
        ----------
        data : Any
            The data to be rendered.
        flags : RenderFlags
            The flags to be used in the rendering.

        Returns
        -------
            The rendered data, which can be a dictionary, list, or string.

        """

        if not (isinstance(data, (str, dict, list)) and data):
            return data

        variables = self.default_variables | self.channel._variables

        if RenderFlags.CUSTOM_ESCAPE in flags:
            variables, changed = Util.custom_escape(variables, escape=True)
            if changed:
                flags |= RenderFlags.CUSTOM_UNESCAPE

        return Util.recursive_render(data=data, variables=variables, flags=flags)

    def get_o_connection(self) -> str:
        """It returns the ID of the next node to be executed.
        Returns
        -------
            The ID of the next node to be executed.
        """
        # Get the next node from the content of node
        try:
            o_connection = self.render_data(self.content.o_connection)
        except AttributeError:
            o_connection = None

        # If the o_connection is None or empty, get the o_connection from the stack
        if o_connection is None or o_connection in ["finish", ""]:
            # If the stack is not empty, get the last node from the stack
            if not self.channel._stack.empty() and self.type != "subroutine":
                self.log.debug(
                    f"[{self.channel.channel_uniqueid}] Getting o_connection from channel stack: {self.channel._stack.queue}"
                )
                o_connection = self.channel._stack.get(timeout=3)

        if o_connection:
            self.log.info(
                f"[{self.channel.channel_uniqueid}] Go to o_connection node in [{self.id}]: '{o_connection}'"
            )

        return o_connection

    async def _update_node(self, o_connection: str = None, cases: list = None):
        """Updates the node in the database.

        Parameters
        ----------
        o_connection : str
            The o_connection of the node.
        cases : list
            The cases of the node.
        """
        channel_state = self.channel.state
        state = None
        validate = cases if cases is not None else o_connection

        if channel_state is ChannelState.HANGUP:
            state = channel_state
        elif not validate:
            state = ChannelState.END

        await self.channel.update_ivr(node_id=o_connection, state=state)

    @classmethod
    @asynccontextmanager
    async def agi_ctx(cls, *, asterisk_conn: Any, http_session: Any):
        token = _agi_ctx_var.set(
            AGIContext(asterisk_conn=asterisk_conn, http_session=http_session)
        )
        try:
            yield
        finally:
            _agi_ctx_var.reset(token)
