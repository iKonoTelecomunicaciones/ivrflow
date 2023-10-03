from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class GetVariable(FlowObject):
    """
    ## GetVariable

    This node returns the value of the indicated variable.

    content:

    ```
    - id: p1
      variable: name_variable
      o_connection: m2
    ```
    """

    variable: str = ib(default="")
    o_connection: str = ib(default=None)
