from __future__ import annotations

from typing import Any, Dict

from attr import dataclass, ib
from mautrix.types import SerializableAttrs
from nodes.node_types import NodeTypes


@dataclass
class FlowObject(SerializableAttrs):
    id: str = ib()
    type: NodeTypes = ib(factory=NodeTypes)
    flow_variables: Dict[str, Any] = {}
