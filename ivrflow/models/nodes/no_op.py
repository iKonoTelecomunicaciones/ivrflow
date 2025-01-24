from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass()
class NoOp(FlowObject):
    """
    ## NoOP

    A no_op node allows print a log message and continue with next node.

    content:

    ```
    - id: p1
      type: no_op
      text: Example log message
      o_connection: m2
    ```
    """

    text: str = ib(default="")
    o_connection: str = ib(default="")

    @staticmethod
    def from_dict(node: dict) -> "NoOp":
        return NoOp(
            id=node.get("id"),
            type=node.get("type"),
            text=node.get("text"),
            o_connection=node.get("o_connection"),
        )
