from typing import Any, Dict

from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class GetFullVariable(FlowObject):
    """
    ## GetFullVariable
    Evaluates a channel expression.
    This node understands complex variable names and builtin variables.
    content:
    ```
    - id: p1
      type: get_full_variable
      variables:
        name: ${var_name_ast}
      o_connection: m2
    ```
    """

    variables: Dict = ib(factory=Dict)
    o_connection: str = ib(default=None)
