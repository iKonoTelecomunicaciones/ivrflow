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


@upgrade_table.register(description="Add stack field to channel table")
async def upgrade_v2(conn: Connection) -> None:
    await conn.execute("ALTER TABLE channel ADD COLUMN stack JSONB NOT NULL DEFAULT '{}'::jsonb")


@upgrade_table.register(description="Add flow table")
async def upgrade_v3(conn: Connection) -> None:
    await conn.execute(
        """CREATE TABLE flow (
            id          SERIAL PRIMARY KEY,
            name        VARCHAR(100) NOT NULL UNIQUE,
            flow        JSONB DEFAULT '{}'::jsonb
        )"""
    )


@upgrade_table.register(description="Add flow_vars column to flow table and add new table module")
async def upgrade_v4(conn: Connection) -> None:

    # Add flow_vars column to flow table
    await conn.execute(
        "ALTER TABLE flow ADD COLUMN IF NOT EXISTS flow_vars JSONB DEFAULT '{}'::jsonb"
    )

    # Create module table
    await conn.execute(
        """CREATE TABLE module (
           id          SERIAL PRIMARY KEY,
           flow_id     INT NOT NULL,
           name        TEXT NOT NULL,
           nodes       JSONB DEFAULT '[]'::jsonb,
           position    JSONB DEFAULT '{}'::jsonb
       )"""
    )

    # Add foreign key to module table
    await conn.execute(
        "ALTER TABLE module ADD CONSTRAINT fk_module_flow FOREIGN KEY (flow_id) REFERENCES flow(id)"
    )

    # Add unique constraint to module table
    await conn.execute(
        "ALTER TABLE module ADD CONSTRAINT idx_unique_module_name_flow_id UNIQUE (name, flow_id)"
    )

    # Create index on module table
    await conn.execute("CREATE INDEX idx_module_flow ON module (flow_id)")


@upgrade_table.register(description="Drop flow column from flow table")
async def upgrade_v5(conn: Connection) -> None:

    # Drop flow column from flow table
    await conn.execute("ALTER TABLE flow DROP COLUMN IF EXISTS flow")


@upgrade_table.register(description="Add new table module_backup")
async def upgrade_v6(conn: Connection) -> None:
    await conn.execute(
        """CREATE TABLE module_backup (
            id          SERIAL PRIMARY KEY,
            flow_id     INT NOT NULL,
            name        TEXT NOT NULL,
            nodes       JSONB DEFAULT '[]'::jsonb,
            position    JSONB DEFAULT '{}'::jsonb,
            created_at  TIMESTAMP WITH TIME ZONE DEFAULT now()
        )"""
    )

    # Create index on module_backup table
    await conn.execute("CREATE INDEX idx_module_backup_flow_id ON module_backup (flow_id)")
