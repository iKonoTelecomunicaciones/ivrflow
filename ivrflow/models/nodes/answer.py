from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class Answer(FlowObject):
    """
    ## Answer channel.

    Answers channel if not already in answer state.
    Returns -1 on channel failure, or 0 if successful.

    content:

    ```
    - id: p1
      type: answer
      o_connection: m2
    ```
    """

    o_connection: str = ib(default="")

    @staticmethod
    def from_dict(node: dict) -> "Answer":
        return Answer(
            id=node.get("id"),
            type=node.get("type"),
            o_connection=node.get("o_connection"),
        )
