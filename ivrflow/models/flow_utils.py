from __future__ import annotations

import logging
from typing import Dict, List

import yaml
from attr import dataclass, ib
from mautrix.types import SerializableAttrs
from mautrix.util.logging import TraceLogger

from .middlewares import HTTPMiddleware

log: TraceLogger = logging.getLogger("ivrflow.models.flow_utils")


@dataclass
class FlowUtils(SerializableAttrs):
    middlewares: List[HTTPMiddleware] = ib(default=[])

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
                HTTPMiddleware(**middleware) for middleware in data.get("middlewares", [])
            ]
        )
