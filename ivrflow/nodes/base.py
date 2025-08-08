from __future__ import annotations

from abc import abstractmethod
from logging import Logger, getLogger
from typing import Any, Dict, List

from aiohttp import ClientSession

from ..channel import Channel
from ..config import Config
from ..utils import Util


def convert_to_int(item: Any) -> Dict | List | int:
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
    session: ClientSession

    def __init__(self, default_variables: Dict, channel: Channel) -> None:
        self.default_variables = default_variables
        self.channel = channel

    @property
    def id(self) -> str:
        return self.content.id

    @property
    def type(self) -> str:
        return self.content.type

    @classmethod
    def init_cls(cls, config: Config, asterisk_conn: ClientSession, session: ClientSession):
        cls.config = config
        cls.asterisk_conn = asterisk_conn
        cls.session = session

    @abstractmethod
    async def run(self):
        pass

    def render_data(self, data: dict | list | str) -> dict | list | str:
        """It renders the data using the default variables and the channel variables.

        Parameters
        ----------
        data : Any
            The data to be rendered.

        Returns
        -------
            The rendered data, which can be a dictionary, list, or string.

        """

        return Util.render_data(
            data=data,
            default_variables=self.default_variables,
            all_variables=self.channel._variables,
        )

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
                    f"Getting o_connection from route stack: {self.channel._stack.queue}"
                )
                o_connection = self.channel._stack.get(timeout=3)

        if o_connection:
            self.log.info(f"Go to o_connection node in [{self.id}]: '{o_connection}'")

        return o_connection
