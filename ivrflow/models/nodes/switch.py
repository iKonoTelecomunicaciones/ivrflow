from typing import Any, Dict, List

from attr import dataclass, ib
from mautrix.types import SerializableAttrs

from ..flow_object import FlowObject


@dataclass
class Case(SerializableAttrs):
    id: str = ib(default=None)
    case: str = ib(default=None)
    variables: Dict[str, Any] = ib(default={})
    o_connection: str = ib(default=None)


@dataclass
class Switch(FlowObject):
    """
    ## Switch

    A switch type node allows to validate the content of a jinja variable,
    and from the result to transit to another node. Example: switch-1
    You can also validate on a case-by-case basis to determine which node to transit to.
    Example: switch-2

    content:

    ```yaml
    - id: switch-1
      type: switch
      validation: '{{ opt }}'
      validation_attempts: 3
      cases:
      - id: 1
        o_connection: m1
      - id: 2
        o_connection: m2
      - id: default
        o_connection: m3
      - id: attempt_exceeded
        o_connection: m4
    ```

    ```yaml
    - id: switch-2
      type: switch
      variable: route.opt
      cases:
      - case: "{% if route.opt == 1 %}True{% else %}False{% endif %}"
        o_connection: m1
      - case: "{% if compare_ratio(route.opt|string, 'hello world')|int >= 80 %}True{% else %}False{% endif %}"
        o_connection: m_hello
      - case: "{% if route.opt|int >= 18 %}True{% else %}False{% endif %}"
        o_connection: m_adult_only
        variables:
          route.active: True
          route.foo: "bar"
      - case: '{% if match("^(0[1-9]|[12][0-9]|3[01])\s(0[1-9]|1[012])\s(19[0-9][0-9]|20[0-9][0-9])$", route.opt) %}True{% else %}False{% endif %}'
        o_connection: m_schedule
      - case: "{% if route.opt == 5 %}True{% else %}False{% endif %}"
        o_connection: m5
    ```
    """

    validation: str = ib(default=None)
    validation_attempts: int = ib(default=None)
    cases: List[Case] = ib(factory=List)

    @classmethod
    def from_dict(cls, data: dict) -> "Switch":
        return cls(
            id=data.get("id"),
            type=data.get("type"),
            validation=data.get("validation"),
            validation_attempts=data.get("validation_attempts"),
            cases=[Case(**case) for case in data.get("cases", [])],
        )
