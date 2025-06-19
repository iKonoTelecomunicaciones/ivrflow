from mautrix.util.async_db import Database

from .channel import Channel
from .flow import Flow
from .migrations import upgrade_table
from .module import Module


def init(db: Database) -> None:
    for table in (Channel, Flow, Module):
        table.db = db


__all__ = ["upgrade_table", "Channel", "Flow", "Module"]
