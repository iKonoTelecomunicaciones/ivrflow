from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class Hangup(FlowObject):
    """
    ## Hangup a channel.

    Hangs up the specified channel.
    If no channel name is given, hangs up the current channel.

    content:

    ```
    - id: p1
      type: hangup
      chan: SIP/XXXXXX
    ```
    """

    chan: str = ib(default="")
