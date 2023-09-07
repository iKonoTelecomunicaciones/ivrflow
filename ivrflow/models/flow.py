from __future__ import annotations

from logging import Logger, getLogger
from typing import Any, Dict, List

import yaml
from attr import dataclass, ib
from mautrix.types import SerializableAttrs

from ..types import NodeType
from .nodes import GetData, HTTPRequest, Playback, Switch

log: Logger = getLogger("ivrflow.models.flow")


@dataclass
class Flow(SerializableAttrs):
    flow_variables: Dict[str, Any] = ib(default={})
    nodes: List[Playback, Switch] = ib(factory=list)

    @classmethod
    def load_flow(cls, path: str) -> "Flow":
        try:
            path = f"/data/flows/{path}.yaml"
            with open(path, "r") as file:
                flow: Dict = yaml.safe_load(file)
            return cls.from_dict(flow)
        except FileNotFoundError:
            log.warning(f"File {path} not found")

    @classmethod
    def from_dict(cls, flow: Dict) -> "Flow":
        return cls(
            flow_variables=flow.get("flow_variables", {}),
            nodes=[cls.initialize_node_dataclass(node) for node in flow.get("nodes", [])],
        )

    @classmethod
    def initialize_node_dataclass(cls, node: Dict) -> Playback | Switch | HTTPRequest | GetData:
        try:
            node_type = NodeType(node.get("type"))
        except ValueError:
            log.warning(f"Node type {node.get('type')} not found")
            return

        if node_type == NodeType.playback:
            return Playback(**node)
        elif node_type == NodeType.switch:
            return Switch.from_dict(node)
        elif node_type == NodeType.http_request:
            return HTTPRequest.from_dict(node)
        elif node_type == NodeType.get_data:
            return GetData.from_dict(node)