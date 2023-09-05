from typing import Dict

from attr import dataclass, ib

from .switch import Case, Switch


@dataclass
class GetData(Switch):
    """
    ## GetData

    A get_data type node allows to get information from the user.

    content:

    ```
      - id: start
        type: get_data
        file: "vm-exten"
        timeout: 5
        max_digits: 1
        variable: opt
        validation: '{{ opt }}'
        cases:
        - id: 1
            o_connection: hello
        - id: default
            o_connection: monkey

    ```
    """

    file: str = ib(factory=str)
    timeout: int = ib(factory=int)
    max_digits: int = ib(factory=int)
    variable: str = ib(factory=str)

    @classmethod
    def from_dict(cls, node: Dict) -> "GetData":
        return cls(
            id=node.get("id"),
            type=node.get("type"),
            file=node.get("file"),
            timeout=node.get("timeout"),
            max_digits=node.get("max_digits"),
            variable=node.get("variable"),
            validation=node.get("validation"),
            cases=[Case(**case) for case in node.get("cases", [])],
        )
