from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class GotoOnExit(FlowObject):
    """
    ## GotoOnExit
    Set endpoint in dialplan on exit.
    content:
    ```
    - id: p1
      type: goto_on_exit
      context: "Incoming"
      extension: "num"
      priority: "1"
    ```
    """

    context: str = ib(default="Incoming")
    extension: str = ib(default="")
    priority: str = ib(default="1")
