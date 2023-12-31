from __future__ import annotations

from attr import dataclass, ib
from mautrix.types import SerializableAttrs


@dataclass
class FlowObject(SerializableAttrs):
    id: str = ib()
    type: str = ib(factory=str)
