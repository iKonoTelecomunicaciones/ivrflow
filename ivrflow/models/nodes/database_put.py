from typing import Dict

from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class DatabasePut(FlowObject):
    """
    ## DatabasePut

    Adds/updates database value

    content:

    ```
      - id: start
        type: database_put
        entries:
          "/Exten/Sequence/199": "{{var_name}}"
          "/Member/Name/899": "{{other_var}}"
        o_connection: m2

    ```
    """

    entries: Dict = ib(factory=Dict)
    o_connection: str = ib(default="")

    @staticmethod
    def from_dict(node: Dict) -> "DatabasePut":
        return DatabasePut(
            id=node.get("id"),
            type=node.get("type"),
            entries=node.get("entries"),
            o_connection=node.get("o_connection"),
        )
