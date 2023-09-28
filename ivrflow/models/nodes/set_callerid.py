from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class SetCallerID(FlowObject):
    """
    ## SetCallerID
    Changes the callerid of the current channel.
    content:
    ```
    - id: CID1
      type: SetCallerID
      number: ""
      o_connection: m2
    ```
    """

    number: int = ib(default=1)
    o_connection: str = ib(default="")
