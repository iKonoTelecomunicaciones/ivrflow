from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

from asyncpg import Record
from attr import dataclass, ib
from mautrix.types import SerializableAttrs
from mautrix.util.async_db import Database

fake_db = Database.create("") if TYPE_CHECKING else None


@dataclass
class ModuleBackup(SerializableAttrs):
    db: ClassVar[Database] = fake_db
    _columns: ClassVar[str] = "flow_id, name, nodes, position, created_at"
    _json_columns: ClassVar[str] = "nodes, position"

    id: int = ib(default=None)
    flow_id: int = ib(factory=int)
    name: str = ib(default=None)
    nodes: dict = ib(factory=dict)
    position: dict = ib(factory=dict)
    created_at: datetime = ib(default=None)

    @property
    def values(self) -> tuple[str, str, str]:
        return self.name, json.dumps(self.nodes), json.dumps(self.position)

    @classmethod
    def _from_row(cls, row: Record) -> ModuleBackup | None:
        return cls(
            id=row["id"],
            flow_id=row["flow_id"],
            name=row["name"],
            nodes=json.loads(row["nodes"]),
            position=json.loads(row["position"]),
            created_at=row["created_at"],
        )

    @classmethod
    async def all_by_flow_id(
        cls, flow_id: int, offset: int = 0, limit: int = 10
    ) -> list["ModuleBackup"]:
        q = f"SELECT id, {cls._columns} FROM module_backup where flow_id=$1 ORDER BY created_at ASC limit $2 offset $3"
        rows = await cls.db.fetch(q, flow_id, limit, offset)
        if not rows:
            return []

        return [cls._from_row(row) for row in rows]

    @classmethod
    async def get_count_by_flow_id(cls, flow_id: int) -> int:
        q = "SELECT count(*) FROM module_backup where flow_id=$1"
        return await cls.db.fetchval(q, flow_id)

    @classmethod
    async def delete_oldest_by_flow_id(cls, flow_id: int):
        q = "DELETE FROM module_backup WHERE created_at = (SELECT MIN(created_at) FROM module_backup WHERE flow_id=$1)"
        await cls.db.execute(q, flow_id)

    @classmethod
    async def get_by_id(cls, id: int) -> ModuleBackup | None:
        q = f"SELECT id, {cls._columns} FROM module_backup WHERE id=$1"
        row = await cls.db.fetchrow(q, id)

        return cls._from_row(row) if row else None

    async def insert(self):
        q = "INSERT INTO module_backup (flow_id, name, nodes, position) VALUES ($1, $2, $3, $4) RETURNING id"
        return await self.db.fetchval(q, self.flow_id, *self.values)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "flow_id": self.flow_id,
            "name": self.name,
            "nodes": self.nodes,
            "position": self.position,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
