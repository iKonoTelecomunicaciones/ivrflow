from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class Answer(FlowObject):
    """
    ## Answer channel.

    Answers channel if not already in answer state.
    Returns -1 on channel failure, or 0 if successful.

    content:

    ```
    - id: p1
      type: answer
      o_connection: m2
    ```
    """

    o_connection: str = ib(default="")
