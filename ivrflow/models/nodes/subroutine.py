from __future__ import annotations

from typing import Dict

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
    def from_dict(node: Dict) -> "Subroutine":

        subroutine = Subroutine(id=node.get("id"), type=node.get("type"))
        for key, value in node.items():
            if key in subroutine.__dict__:
                subroutine.__dict__[key] = value
        return subroutine
