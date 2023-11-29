from typing import Dict

from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class Playback(FlowObject):
    """
    ## Playback

    A playback node allows an audio to be streamed.

    content:

    ```
    - id: p1
      type: playback
      text: "Hello, this is a test"
      file: "tt-monkeys"
      middleware: m1
      scape_digits: "1234567890*#"
      sample_offset: 1000
      o_connection: m2
    ```
    """

    file: str = ib(default="")
    text: str = ib(default=None)
    middleware: Dict = ib(default=None)
    escape_digits: str = ib(default="")
    sample_offset: int = ib(default=0)
    o_connection: str = ib(default="")
