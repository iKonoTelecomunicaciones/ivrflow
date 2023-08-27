from __future__ import annotations

from abc import abstractmethod
from json import JSONDecodeError, dumps, loads
from logging import Logger, getLogger
from typing import Any, Dict, List

from aiohttp import ClientSession

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
        if item.lower() == "true":
            return True
        elif item.lower() == "false":
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
    elif isinstance(item, str) and item.isdigit():
        return int(item)
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

    def __init__(self, default_variables: Dict) -> None:
        self.default_variables = default_variables

    @property
    def id(self) -> str:
        return self.content.id

    @property
    def type(self) -> str:
        return self.content.type

    @classmethod
    def init_cls(cls, config: Config, asterisk_conn: ClientSession):
        cls.config = config
        cls.asterisk_conn = asterisk_conn

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

        copy_variables = {**self.default_variables}

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
