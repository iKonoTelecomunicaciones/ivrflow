from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class GetVariable(FlowObject):
    """
    ## GetVariable

    Get a channel variable.

    This node returns the value of the indicated channel variable.

    content:

    ```
    - id: p1
      type: get_variable
      name: var_name_ast
      variable: var_name_result
      o_connection: m2
    ```
    """

    name: str = ib(default="")
    variable: str = ib(factory=str)
    o_connection: str = ib(default=None)
