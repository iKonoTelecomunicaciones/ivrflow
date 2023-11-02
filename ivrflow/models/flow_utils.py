from __future__ import annotations

import logging
from typing import Dict, List

import yaml
from attr import dataclass, ib
from mautrix.types import SerializableAttrs
from mautrix.util.logging import TraceLogger

from ..types import MiddlewareType
from .middlewares import ASRMiddleware, EmailServer, HTTPMiddleware, TTSMiddleware

log: TraceLogger = logging.getLogger("ivrflow.models.flow_utils")


@dataclass
class FlowUtils(SerializableAttrs):
    middlewares: List[HTTPMiddleware] = ib(default=[])
    email_servers: List[Dict] = ib(default=[])

    @classmethod
    def load_flow_utils(cls) -> "FlowUtils":
        try:
            path = f"/data/flow_utils.yaml"
            with open(path, "r") as file:
                flow_utils: Dict = yaml.safe_load(file)
            return cls.from_dict(flow_utils)
        except FileNotFoundError:
            log.warning("File flow_utils.yaml not found")

    @classmethod
    def from_dict(cls, data: Dict) -> "FlowUtils":
        return cls(
            middlewares=[
                cls.initialize_middleware_dataclass(middleware)
                for middleware in data.get("middlewares", [])
            ],
            email_servers=[
                cls.initialize_email_server_dataclass(email_server)
                for email_server in data.get("email_servers", [])
            ],
        )

    @classmethod
    def initialize_middleware_dataclass(cls, middleware: Dict) -> HTTPMiddleware | TTSMiddleware:
        try:
            middleware_type = MiddlewareType(middleware.get("type"))
        except ValueError:
            log.warning(f"Middleware type {middleware.get('type')} not found")
            return

        if middleware_type in (MiddlewareType.jwt, MiddlewareType.basic):
            return HTTPMiddleware(**middleware)
        elif middleware_type == MiddlewareType.tts:
            return TTSMiddleware(**middleware)
        elif middleware_type == MiddlewareType.asr:
            return ASRMiddleware(**middleware)
        else:
            log.warning(f"Middleware type {middleware_type} not found")
            return

    @classmethod
    def initialize_email_server_dataclass(cls, email_server: Dict) -> EmailServer:
        return EmailServer(**email_server)
