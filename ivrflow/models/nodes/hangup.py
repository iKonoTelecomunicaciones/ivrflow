from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class Hangup(FlowObject):
    """
    ## Hangup a channel.

    Hangs up the specified channel.

    content:

    ```
    - id: p1
      type: hangup
      chan: SIP/101-123456789
    ```
    """

    chan: str = ib(default="")
    o_connection: str = ib(default=None)
