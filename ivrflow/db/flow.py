import json
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional

from asyncpg import Record
from attr import dataclass, ib
from mautrix.types import SerializableAttrs
from mautrix.util.async_db import Database

fake_db = Database.create("") if TYPE_CHECKING else None


@dataclass
class Flow(SerializableAttrs):
    db: ClassVar[Database] = fake_db

    id: int = ib(default=None)
    name: str = ib(factory=str)
    flow_vars: dict = ib(factory=dict)

    __columns = "id, name, flow_vars"

    @property
    def values(self) -> Dict[str, Any]:
        return (self.name, json.dumps(self.flow_vars))

    @classmethod
    def _from_row(cls, row: Record) -> Optional["Flow"]:
        return cls(id=row["id"], name=row["name"], flow_vars=json.loads(row["flow_vars"]))

    @classmethod
    async def all(cls) -> list[Dict]:
        q = f"SELECT {cls.__columns} FROM flow"
        rows = await cls.db.fetch(q)
        if not rows:
            return []

        return [cls._from_row(row).serialize() for row in rows]

    @classmethod
    async def get_by_id(cls, id: int) -> Optional["Flow"]:
        q = f"SELECT {cls.__columns} FROM flow WHERE id=$1"
        row = await cls.db.fetchrow(q, id)

        if not row:
            return

        return cls._from_row(row)

    @classmethod
    async def get_by_name(cls, name: str) -> Optional["Flow"]:
        q = f"SELECT {cls.__columns} FROM flow WHERE name=$1"
        row = await cls.db.fetchrow(q, name)

        if not row:
            return

        return cls._from_row(row)

    async def insert(self) -> int:
        q = "INSERT INTO flow (name, flow_vars) VALUES ($1, $2) RETURNING id"
        return await self.db.fetchval(q, *self.values)

    async def update(self) -> None:
        q = "UPDATE flow SET name=$1, flow_vars=$2 WHERE id=$3"
        await self.db.execute(q, *self.values, self.id)

    @classmethod
    async def check_exists(cls, id: int) -> bool:
        q = "SELECT EXISTS(SELECT 1 FROM flow WHERE id=$1)"
        return await cls.db.fetchval(q, id)
