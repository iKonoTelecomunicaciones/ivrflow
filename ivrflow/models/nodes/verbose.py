from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class Verbose(FlowObject):
    """
    ## Verbose
    Logs a message to the asterisk verbose log.
    content:
    ```
    - id: v1
      type: Verbose
      message: ""
      level: 1
      o_connection: m2
    ```
    """

    message: str = ib(default="")
    level: int = ib(default=1)
    o_connection: str = ib(default="")

    @staticmethod
    def from_dict(node: dict) -> "Verbose":
        return Verbose(
            id=node.get("id"),
            type=node.get("type"),
            message=node.get("message"),
            level=node.get("level"),
            o_connection=node.get("o_connection"),
        )
