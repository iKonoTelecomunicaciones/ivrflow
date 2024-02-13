from __future__ import annotations

from abc import abstractmethod
from json import JSONDecodeError, dumps, loads
from logging import Logger, getLogger
from typing import Any, Dict, List

from aiohttp import ClientSession

from ..channel import Channel
from ..config import Config
from ..jinja.jinja_template import jinja_env


def convert_to_bool(item) -> Dict | List | str:
    if isinstance(item, dict):
        for k, v in item.items():
            item[k] = convert_to_bool(v)
        return item
    elif isinstance(item, list):
        return [convert_to_bool(i) for i in item]
    elif isinstance(item, str):
        if item.strip().lower() == "true":
            return True
        elif item.strip().lower() == "false":
            return False
        else:
            return item
    else:
        return item


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
        item = convert_to_bool(item)

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

    def render_data(self, data: Dict | List | str) -> Dict | List | str:
        """It takes a dictionary or list, converts it to a string,
        and then uses Jinja to render the string

        Parameters
        ----------
        data : Dict | List
            The data to be rendered.

        Returns
        -------
            A dictionary or list.

        """

        if isinstance(data, str):
            data_template = jinja_env.from_string(data)
        else:
            try:
                data_template = jinja_env.from_string(dumps(data))
            except Exception as e:
                self.log.exception(e)
                return

        copy_variables = {**self.default_variables, **self.channel._variables}

        try:
            data = loads(data_template.render(**copy_variables))
            data = convert_to_bool(data)
            return data
        except JSONDecodeError:
            data = data_template.render(**copy_variables)
            return convert_to_bool(data)
        except KeyError:
            data = loads(data_template.render())
            data = convert_to_bool(data)
            return data

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
