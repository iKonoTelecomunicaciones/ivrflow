from __future__ import annotations

from logging import Logger, getLogger
from typing import Any, Dict, List, Union

import yaml
from attr import dataclass, ib
from mautrix.types import SerializableAttrs

from ..config import config
from ..db import Flow as DBFlow
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
    Playback,
    Record,
    SetCallerID,
    SetMusic,
    SetVariable,
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
            return cls.from_dict(flow)
        except FileNotFoundError:
            log.warning(f"File {path} not found")

    @classmethod
    async def load_from_database(cls, flow_name: str) -> "Flow":
        log.info(f"Loading flow {flow_name} from database")
        flow = await DBFlow.get_by_name(flow_name)
        return cls.from_dict(flow.flow)

    @classmethod
    async def load_flow(cls, flow_name: str) -> "Flow":
        if config["ivrflow.load_flow_from"] == "yaml":
            flow = cls.load_from_yaml(flow_name)
        else:
            flow = await cls.load_from_database(flow_name)

        return flow

    @classmethod
    def from_dict(cls, flow: Dict) -> "Flow":
        return cls(
            flow_variables=flow.get("flow_variables", {}),
            nodes=[cls.initialize_node_dataclass(node) for node in flow.get("nodes", [])],
        )

    @classmethod
    def initialize_node_dataclass(cls, node: Dict) -> Node:
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
        elif node_type == NodeType.set_variable:
            return SetVariable(**node)
        elif node_type == NodeType.record:
            return Record(**node)
        elif node_type == NodeType.hangup:
            return Hangup(**node)
        elif node_type == NodeType.set_music:
            return SetMusic(**node)
        elif node_type == NodeType.verbose:
            return Verbose(**node)
        elif node_type == NodeType.set_callerid:
            return SetCallerID(**node)
        elif node_type == NodeType.exec_app:
            return ExecApp(**node)
        elif node_type == NodeType.database_get:
            return DatabaseGet(**node)
        elif node_type == NodeType.get_full_variable:
            return GetFullVariable(**node)
        elif node_type == NodeType.database_del:
            return DatabaseDel(**node)
        elif node_type == NodeType.email:
            return Email(**node)
        elif node_type == NodeType.database_put:
            return DatabasePut(**node)
        elif node_type == NodeType.answer:
            return Answer(**node)
        elif node_type == NodeType.goto_on_exit:
            return GotoOnExit(**node)
        elif node_type == NodeType.subroutine:
            return Subroutine(**node)
