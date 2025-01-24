from typing import Dict

from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class DatabaseGet(FlowObject):
    """
    ## DatabaseGet

    Gets database value.

    content:

    ```
      - id: start
        type: database_get
        variables:
          var_name: "/Exten/SIP/199"
          other_var: "/Member/Name/899"
        o_connection: m2

    ```
    """

    variables: Dict = ib(factory=Dict)
    o_connection: str = ib(default="")

    @staticmethod
    def from_dict(node: Dict) -> "DatabaseGet":
        return DatabaseGet(
            id=node.get("id"),
            type=node.get("type"),
            variables=node.get("variables"),
            o_connection=node.get("o_connection"),
        )
