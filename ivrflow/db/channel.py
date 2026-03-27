from __future__ import annotations

import json
from enum import Enum
from queue import LifoQueue
from typing import TYPE_CHECKING, ClassVar

from asyncpg import Record
from attr import dataclass, ib
from mautrix.util.async_db import Database

from ..types import ChannelUniqueID

fake_db = Database.create("") if TYPE_CHECKING else None


class ChannelState(Enum):
    START = "start"
    END = "end"
    HANGUP = "hangup"


@dataclass
class Channel:
    db: ClassVar[Database] = fake_db

    id: int
    channel_uniqueid: ChannelUniqueID
    variables: str
    node_id: str
    state: ChannelState | str | None = ib(default=None)
    stack: str = ib(default="{}")

    _columns = "channel_uniqueid, variables, node_id, state, stack"

    @property
    def values(self) -> tuple:
        return (
            self.channel_uniqueid,
            self.variables,
            self.node_id,
            self.state.value if isinstance(self.state, ChannelState) else self.state,
            self.stack,
        )

    @property
    def _stack(self) -> LifoQueue | None:
        stack: LifoQueue = LifoQueue(maxsize=255)
        if self.stack:
            try:
                stack_dict = json.loads(self.stack)
                stack.queue = stack_dict[self.channel_uniqueid] if stack_dict else []
            except KeyError:
                stack.queue = []
        return stack

    @classmethod
    def _from_row(cls, row: Record) -> Channel | None:
        data = {**row}
        try:
            state = ChannelState(data.pop("state"))
        except ValueError:
            state = ""

        return cls(state=state, **data)

    @classmethod
    async def get_by_channel_uniqueid(cls, channel_uniqueid: ChannelUniqueID) -> Channel | None:
        q = f"SELECT id, {cls._columns} FROM channel WHERE channel_uniqueid=$1"
        row = await cls.db.fetchrow(q, channel_uniqueid)

        return cls._from_row(row) if row else None

    async def insert(self) -> str:
        q = f"INSERT INTO channel ({self._columns}) VALUES ($1, $2, $3, $4, $5)"
        await self.db.execute(q, *self.values)

    @property
    def _variables(self) -> dict:
        if not hasattr(self, "_vars_cache"):
            self._vars_cache: dict = json.loads(self.variables or "{}")
        return self._vars_cache

    def flush_vars(self):
        if hasattr(self, "_vars_cache"):
            self.variables = json.dumps(self._vars_cache)

    async def update(self) -> None:
        self.flush_vars()
        q = (
            "UPDATE channel SET variables = $2, node_id = $3, state = $4, stack=$5 "
            "WHERE channel_uniqueid = $1"
        )
        await self.db.execute(q, *self.values)

    async def update_variables(self) -> None:
        self.flush_vars()
        q = "UPDATE channel SET variables = $2 WHERE channel_uniqueid = $1"
        await self.db.execute(q, self.channel_uniqueid, self.variables)
