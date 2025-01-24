from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class ExecApp(FlowObject):
    """
    ## ExecApp
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

    @staticmethod
    def from_dict(node: dict) -> "ExecApp":
        return ExecApp(
            id=node.get("id"),
            type=node.get("type"),
            application=node.get("application"),
            options=node.get("options"),
            o_connection=node.get("o_connection"),
        )
