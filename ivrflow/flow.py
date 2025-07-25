from __future__ import annotations

import logging
from typing import Dict, List, Optional, Union

from mautrix.util.logging import TraceLogger

from .channel import Channel
from .flow_utils import FlowUtils
from .middlewares import ASRMiddleware, HTTPMiddleware, TTSMiddleware
from .models import Flow as FlowModel
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
from .types import MiddlewareType, NodeType

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


class Flow:
    log: TraceLogger = logging.getLogger("ivrflow.flow")
    flow_utils: FlowUtils

    def __init__(self) -> None:
        self.data: FlowModel = None
        self.nodes: List[Node] = []
        self.nodes_by_id: Dict[str, Node] = {}

    async def load_flow(self, flow_name: str):
        self.data = await FlowModel.load_flow(flow_name=flow_name)
        self.nodes = self.data.nodes or []
        self.nodes_by_id: Dict[str, Dict] = {}

    @property
    def flow_variables(self) -> Dict:
        return self.data.flow_variables

    @classmethod
    def init_cls(cls, flow_utils: FlowUtils) -> None:
        cls.flow_utils = flow_utils

    def _add_node_to_cache(self, node_data: Node):
        self.nodes_by_id[node_data.id] = node_data

    def get_node_by_id(self, node_id: str) -> Node | None:
        """This function returns a node from a cache or a list of nodes based on its ID.

        Parameters
        ----------
        node_id : str
            The ID of the node that we want to retrieve from the graph.

        Returns
        -------
            This function returns a dictionary object representing a node in a graph, or `None`
            if the node with the given ID is not found.

        """

        try:
            return self.nodes_by_id[node_id]
        except KeyError:
            pass

        for node in self.nodes:
            if node_id == node.id:
                self._add_node_to_cache(node)
                return node

    def middleware(self, middleware_id: str, channel: Channel) -> HTTPMiddleware:
        middleware_model = self.flow_utils.get_middleware_by_id(middleware_id=middleware_id)

        if not middleware_model:
            return

        try:
            middleware_type = MiddlewareType(middleware_model.type)
        except ValueError:
            self.log.error(f"Middleware type {middleware_model.type} is not supported.")
            return

        if middleware_type in (MiddlewareType.jwt, MiddlewareType.basic):
            middleware_initialized = HTTPMiddleware(
                http_middleware_content=middleware_model,
                channel=channel,
                default_variables=self.flow_variables,
            )
        elif middleware_type == MiddlewareType.tts:
            middleware_initialized = TTSMiddleware(
                tts_middleware_content=middleware_model,
                channel=channel,
                default_variables=self.flow_variables,
            )
        elif middleware_type == MiddlewareType.asr:
            middleware_initialized = ASRMiddleware(
                asr_middleware_content=middleware_model,
                channel=channel,
                default_variables=self.flow_variables,
            )

        return middleware_initialized

    def node(self, channel: Channel) -> Optional[Node]:
        node_data = self.get_node_by_id(node_id=channel.node_id)

        if not node_data:
            return

        try:
            node_type = NodeType(node_data.type)
        except ValueError:
            self.log.error(f"Node type {node_data.type} is not supported.")
            return

        if node_type == NodeType.playback:
            node_initialized = Playback(
                playback_content=node_data, default_variables=self.flow_variables, channel=channel
            )
            if node_data.middleware:
                middleware_id = list(node_data.middleware.keys())[0]
                middleware = self.middleware(middleware_id, channel=channel)
                node_initialized.middleware = middleware
        elif node_type == NodeType.switch:
            node_initialized = Switch(
                switch_content=node_data, default_variables=self.flow_variables, channel=channel
            )
        elif node_type == NodeType.http_request:
            node_initialized = HTTPRequest(
                http_request_content=node_data,
                default_variables=self.flow_variables,
                channel=channel,
            )
            if node_data.middleware:
                middleware = self.middleware(node_data.middleware, channel=channel)
                node_initialized.middleware = middleware
        elif node_type == NodeType.get_data:
            node_initialized = GetData(
                get_data_content=node_data, channel=channel, default_variables=self.flow_variables
            )
            if node_data.middlewares:
                middlewares = []
                for key, _ in node_data.middlewares.items():
                    middlewares.append(self.middleware(key, channel=channel))
                node_initialized.middlewares = middlewares
        elif node_type == NodeType.set_variable:
            node_initialized = SetVariable(
                set_variable_content=node_data,
                default_variables=self.flow_variables,
                channel=channel,
            )
        elif node_type == NodeType.record:
            node_initialized = Record(
                record_content=node_data, default_variables=self.flow_variables, channel=channel
            )
        elif node_type == NodeType.hangup:
            node_initialized = Hangup(
                hangup_content=node_data,
                default_variables=self.flow_variables,
                channel=channel,
            )
        elif node_type == NodeType.set_music:
            node_initialized = SetMusic(
                set_music_content=node_data,
                default_variables=self.flow_variables,
                channel=channel,
            )
        elif node_type == NodeType.verbose:
            node_initialized = Verbose(
                verbose_content=node_data, default_variables=self.flow_variables, channel=channel
            )
        elif node_type == NodeType.set_callerid:
            node_initialized = SetCallerID(
                set_callerid_content=node_data,
                default_variables=self.flow_variables,
                channel=channel,
            )
        elif node_type == NodeType.exec_app:
            node_initialized = ExecApp(
                exec_app_content=node_data,
                default_variables=self.flow_variables,
                channel=channel,
            )
        elif node_type == NodeType.database_get:
            node_initialized = DatabaseGet(
                database_get_content=node_data,
                default_variables=self.flow_variables,
                channel=channel,
            )
        elif node_type == NodeType.get_full_variable:
            node_initialized = GetFullVariable(
                get_full_variable_content=node_data,
                default_variables=self.flow_variables,
                channel=channel,
            )

        elif node_type == NodeType.database_del:
            node_initialized = DatabaseDel(
                database_del_content=node_data,
                default_variables=self.flow_variables,
                channel=channel,
            )
        elif node_type == NodeType.email:
            node_initialized = Email(
                email_content=node_data,
                default_variables=self.flow_variables,
                channel=channel,
            )
        elif node_type == NodeType.database_put:
            node_initialized = DatabasePut(
                database_put_content=node_data,
                default_variables=self.flow_variables,
                channel=channel,
            )
        elif node_type == NodeType.answer:
            node_initialized = Answer(
                answer_content=node_data,
                default_variables=self.flow_variables,
                channel=channel,
            )
        elif node_type == NodeType.goto_on_exit:
            node_initialized = GotoOnExit(
                goto_on_exit_content=node_data,
                default_variables=self.flow_variables,
                channel=channel,
            )
        elif node_type == NodeType.subroutine:
            node_initialized = Subroutine(
                subroutine_node_data=node_data,
                default_variables=self.flow_variables,
                channel=channel,
            )
        elif node_type == NodeType.no_op:
            node_initialized = NoOp(
                no_op_content=node_data,
                default_variables=self.flow_variables,
                channel=channel,
            )
        elif node_type == NodeType.set_vars:
            node_initialized = SetVars(
                default_variables=self.flow_variables,
                set_vars_content=node_data,
                channel=channel,
            )
        else:
            return

        return node_initialized
