from asyncpg import Connection
from mautrix.util.async_db import UpgradeTable

upgrade_table = UpgradeTable()


@upgrade_table.register(description="Initial revision")
async def upgrade_v1(conn: Connection) -> None:
    await conn.execute(
        """CREATE TABLE channel (
            id                  SERIAL PRIMARY KEY,
            channel_uniqueid    TEXT NOT NULL,
            variables           JSON,
            node_id             TEXT,
            state               TEXT
        )"""
    )

    await conn.execute(
        "ALTER TABLE channel ADD CONSTRAINT idx_unique_channel_uniqueid UNIQUE (channel_uniqueid)"
    )
