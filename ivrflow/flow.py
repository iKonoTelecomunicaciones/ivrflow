from __future__ import annotations

import logging
from typing import Dict, Optional

from mautrix.util.logging import TraceLogger

from .channel import Channel
from .flow_utils import FlowUtils
from .middlewares import ASRMiddleware, HTTPMiddleware, TTSMiddleware
from .models import Flow as FlowModel
from .nodes import (
    Answer,
    DatabaseDel,
    DatabasePut,
    Email,
    Exec_App,
    GetData,
    GetFullVariable,
    Hangup,
    HTTPRequest,
    Playback,
    Record,
    SetCallerID,
    SetMusic,
    SetVariable,
    Switch,
    Verbose,
)
from .types import MiddlewareType, NodeType


class Flow:
    log: TraceLogger = logging.getLogger("ivrflow.flow")

    nodes: Dict[str, object]
    nodes_by_id: Dict[str, object] = {}

    def __init__(self, *, flow_data: FlowModel, flow_utils: Optional[FlowUtils] = None) -> None:
        self.content: FlowModel = flow_data
        self.nodes = self.content.nodes
        self.flow_utils = flow_utils

    def _add_node_to_cache(
        self,
        node_data: Playback
        | Switch
        | HTTPRequest
        | GetData
        | SetVariable
        | Record
        | Hangup
        | SetMusic
        | Verbose
        | SetCallerID
        | Email
        | Exec_App
        | GetFullVariable
        | DatabaseDel
        | DatabasePut
        | Answer,
    ):
        self.nodes_by_id[node_data.id] = node_data

    @property
    def flow_variables(self) -> Dict:
        return self.content.flow_variables

    def get_node_by_id(self, node_id: str) -> object | None:
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

    def node(
        self, channel: Channel
    ) -> (
        Playback
        | Switch
        | Email
        | HTTPRequest
        | GetData
        | SetVariable
        | Record
        | Hangup
        | SetMusic
        | Verbose
        | SetCallerID
        | Exec_App
        | GetFullVariable
        | DatabaseDel
        | DatabasePut
        | Answer
        | None
    ):
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
                middleware = self.middleware(node_data.middleware, channel=channel)
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

            if node_data.middleware:
                if isinstance(node_data.middleware, list):
                    middleware = []
                    for middleware_id in node_data.middleware:
                        middleware.append(self.middleware(middleware_id, channel=channel))
                else:
                    middleware = self.middleware(node_data.middleware, channel=channel)

                node_initialized.middleware = middleware
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
            node_initialized = Exec_App(
                exec_app_content=node_data,
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
                email_content=node_data, default_variables=self.flow_variables, channel=channel
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
        else:
            return

        return node_initialized
