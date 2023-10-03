from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class Exec_App(FlowObject):
    """
    ## Exec_App
    Logs a message to the asterisk verbose log.
    content:
    ```
    - id: v1
      type: exec_app
      application: "Dial"
      options: "SIP/301"
      o_connection: m2
    ```
    """

    application: str = ib(default="")
    options: str = ib(default="")
    o_connection: str = ib(default="")
