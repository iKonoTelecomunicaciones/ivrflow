from mautrix.util.async_db import Database

from .channel import Channel
from .migrations import upgrade_table


def init(db: Database) -> None:
    Channel.db = db


__all__ = ["upgrade_table", "Channel"]
