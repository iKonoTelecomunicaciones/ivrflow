from __future__ import annotations

from logging import Logger, getLogger
from typing import Any, Dict, List, Union

import yaml
from attr import dataclass, ib
from mautrix.types import SerializableAttrs

from ..config import config
from ..db import Flow as DBFlow
from ..db import Module as DBModule
from ..types import NodeType
from .nodes import (
    Answer,
    DatabaseDel,
    DatabaseGet,
    DatabasePut,
    Email,
    ExecApp,
    GetData,
    GetFullVariable,
    GotoOnExit,
    Hangup,
    HTTPRequest,
    NoOp,
    Playback,
    Record,
    SetCallerID,
    SetMusic,
    SetVariable,
    SetVars,
    Subroutine,
    Switch,
    Verbose,
)

Node = Union[
    Answer,
    DatabaseDel,
    DatabaseGet,
    DatabasePut,
    Email,
    ExecApp,
    GetData,
    GetFullVariable,
    GotoOnExit,
    Hangup,
    HTTPRequest,
    Playback,
    Record,
    SetCallerID,
    SetMusic,
    SetVariable,
    Subroutine,
    Switch,
    Verbose,
    NoOp,
    SetVars,
]

log: Logger = getLogger("ivrflow.models.flow")


@dataclass
class Flow(SerializableAttrs):
    flow_variables: Dict[str, Any] = ib(default={})
    nodes: List[Playback, Switch] = ib(factory=list)

    @classmethod
    def load_from_yaml(cls, flow_name: str) -> "Flow":
        log.info(f"Loading flow {flow_name} from yaml")
        try:
            path = f"/data/flows/{flow_name}.yaml"
            with open(path, "r") as file:
                flow: Dict = yaml.safe_load(file)
            return cls.from_dict(flow.get("flow_variables", {}), flow.get("nodes", []))
        except FileNotFoundError:
            log.warning(f"File {path} not found")

    @classmethod
    async def load_from_database(cls, flow_name: str) -> "Flow":
        log.info(f"Loading flow {flow_name} from database")
        flow = await DBFlow.get_by_name(flow_name)
        modules = await DBModule.all(flow_id=flow.id)
        nodes = [node for module in modules for node in module.get("nodes", [])]

        return cls.from_dict(flow.flow_vars, nodes)

    @classmethod
    async def load_flow(cls, flow_name: str) -> "Flow":
        if config["ivrflow.load_flow_from"] == "yaml":
            flow = cls.load_from_yaml(flow_name)
        else:
            flow = await cls.load_from_database(flow_name)

        return flow

    @classmethod
    def from_dict(cls, flow_vars: dict, nodes: list[dict]) -> "Flow":
        return cls(
            flow_variables=flow_vars,
            nodes=[cls.initialize_node_dataclass(node) for node in nodes],
        )

    @classmethod
    def initialize_node_dataclass(cls, node: Dict) -> Node:
        try:
            node_type = NodeType(node.get("type"))
        except ValueError:
            log.warning(f"Node type {node.get('type')} not found")
            return

        node_class: dict[NodeType, Node] = {
            NodeType.playback: Playback,
            NodeType.switch: Switch,
            NodeType.http_request: HTTPRequest,
            NodeType.get_data: GetData,
            NodeType.set_variable: SetVariable,
            NodeType.record: Record,
            NodeType.hangup: Hangup,
            NodeType.set_music: SetMusic,
            NodeType.verbose: Verbose,
            NodeType.set_callerid: SetCallerID,
            NodeType.exec_app: ExecApp,
            NodeType.database_get: DatabaseGet,
            NodeType.get_full_variable: GetFullVariable,
            NodeType.database_del: DatabaseDel,
            NodeType.email: Email,
            NodeType.database_put: DatabasePut,
            NodeType.answer: Answer,
            NodeType.goto_on_exit: GotoOnExit,
            NodeType.subroutine: Subroutine,
            NodeType.no_op: NoOp,
            NodeType.set_vars: SetVars,
        }

        return node_class[node_type].from_dict(node)
