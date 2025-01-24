from __future__ import annotations

from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class Subroutine(FlowObject):
    """
    ## Subroutine
    The subroutine node allows common threads to be carried out in a menu flow.
    Example:
    ```
    - id: sub1
      type: subroutine
      go_sub: subroutine_foo
      o_connection: m2
    ```
    """

    go_sub: str = ib(default=None)
    o_connection: str = ib(default=None)

    @staticmethod
    def from_dict(node: dict) -> Subroutine:
        return Subroutine(
            id=node.get("id"),
            type=node.get("type"),
            go_sub=node.get("go_sub"),
            o_connection=node.get("o_connection"),
        )
