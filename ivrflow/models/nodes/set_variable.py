from typing import Dict

from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class SetVariable(FlowObject):
    variables: Dict = ib(factory=Dict)
    o_connection: str = ib(default=None)

    @staticmethod
    def from_dict(node: Dict) -> "SetVariable":
        return SetVariable(
            id=node.get("id"),
            type=node.get("type"),
            variables=node.get("variables"),
            o_connection=node.get("o_connection"),
        )
