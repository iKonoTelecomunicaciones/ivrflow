from attr import dataclass, ib
from ..flow_object import FlowObject
from nodes.node_types import NodeTypes
from typing import Dict, Any


@dataclass
class Playback(FlowObject):
    """
    ## Playback

    A playback node allows an audio to be streamed.

    content:

    ```
    - id: p1
      type: playback
      file: "tt-monkeys"
      scape_digits: "1234567890*#"
      sample_offset: 1000
      o_connection: m2
    ```
    """

    file: str = ib(default="")
    scape_digits: str = ib(default="")
    sample_offset: int = ib(default=0)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FlowObject:
        return cls(
            id=data["id"],
            type=NodeTypes(data["type"]),
            flow_variables=data.get("flow_variables", {}),
            file=data.get("file", ""),
            scape_digits=data.get("scape_digits", ""),
            sample_offset=data.get("sample_offset", 0),
        )
