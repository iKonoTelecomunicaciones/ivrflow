from typing import Dict

from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class SetVariable(FlowObject):
    variables: Dict = ib(factory=Dict)
    o_connection: str = ib(default=None)
