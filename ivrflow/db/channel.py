from typing import TYPE_CHECKING, ClassVar

from attr import dataclass
from mautrix.util.async_db import Database

fake_db = Database.create("") if TYPE_CHECKING else None


@dataclass
class Channel:
    db: ClassVar[Database] = fake_db
