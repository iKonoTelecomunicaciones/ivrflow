from typing import Dict

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
          "/Exten/Sequence/196"
          "/Exten/Sequence/197"
        o_connection: m2

    ```
    """

    entries: str = ib(default=str)
    o_connection: str = ib(default="")
