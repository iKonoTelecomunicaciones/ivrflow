from typing import Any, Dict

from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class ASRMiddleware(FlowObject):
    """
    ## ASRMiddleware

    A ASR middleware node allows to recognize text from a sound file.

    content:

    ```
    - id: m1
      type: asr
      method: GET
      url: "http://localhost:5000/asr"
      text: "{{ content }}"
      variables:
          content: "text"
      cookies:
          cookie1: "value1"
      query_params:
          param1: "value1"
      headers:
          header1: "value1"
      basic_auth:
          username: "user"
          password: "pass"
      data:
          data1: "value1"
      json:
          json1: "value1"
    """

    method: str = ib(default=None)
    url: str = ib(default=None)
    text: str = ib(default=None)
    variables: Dict[str, Any] = ib(factory=dict)
    cookies: Dict[str, Any] = ib(factory=dict)
    query_params: Dict[str, Any] = ib(factory=dict)
    headers: Dict[str, Any] = ib(factory=dict)
    basic_auth: Dict[str, Any] = ib(factory=dict)
    data: Dict[str, Any] = ib(factory=dict)
    json: Dict[str, Any] = ib(factory=dict)
