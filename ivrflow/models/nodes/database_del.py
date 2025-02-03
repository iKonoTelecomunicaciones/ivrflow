from typing import List

from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class DatabaseDel(FlowObject):
    """
    ## DatabaseDel

    Removes database key/value.

    content:

    ```
      - id: start
        type: database_del
        entries:
          - "/Exten/Sequence/196"
          - "/Exten/Sequence/197"
        o_connection: m2

    ```
    """

    entries: List[str] = ib(default=List[str])
    o_connection: str = ib(default="")

    @staticmethod
    def from_dict(node: dict) -> "DatabaseDel":
        return DatabaseDel(
            id=node.get("id"),
            type=node.get("type"),
            entries=node.get("entries"),
            o_connection=node.get("o_connection"),
        )
