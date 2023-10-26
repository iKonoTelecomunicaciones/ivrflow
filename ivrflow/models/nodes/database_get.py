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
        family: "family"
        key: "key"
        variable: return_database_get
        o_connection: m2

    ```
    """

    family: str = ib(default="")
    key: str = ib(default="")
    variable: str = ib(default="")
    o_connection: str = ib(default="")
