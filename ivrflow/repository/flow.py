from logging import Logger, getLogger
from typing import Any, Dict, List

import yaml
from attr import dataclass, ib
from mautrix.types import SerializableAttrs

from .nodes import Playback

log: Logger = getLogger("ivrflow.repository.flow")


@dataclass
class Flow(SerializableAttrs):
    flow_variables: Dict[str, Any] = ib(default={})
    nodes: List[Playback] = ib(factory=list)
    # middlewares: List[HTTPMiddleware] = ib(default=[])

    @classmethod
    def load_flow(cls, path: str):
        try:
            path = f"/data/flows/{path}.yaml"
            with open(path, "r") as file:
                flow: Dict = yaml.safe_load(file)
            return cls.from_dict(flow)
        except FileNotFoundError:
            log.warning(f"File {path} not found")

    @classmethod
    def from_dict(cls, flow: Dict):
        return cls(
            flow_variables=flow.get("flow_variables", {}),
            nodes=[Playback(**node) for node in flow.get("nodes", [])],
        )
