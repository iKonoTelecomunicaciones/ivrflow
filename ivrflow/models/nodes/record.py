from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class Record(FlowObject):
    """
    ## Record

    A Record node allows recording to a given file.

    content:

    ```
    - id: p1
      type: record
      file: "{{ record_file }}"
      format: "wav"
      escape_digits: "1234567890*#"
      offset: 0
      timeout: 20000
      silence: 2000
      beep: beep
      o_connection: m2
    ```
    """

    file: str = ib(default="")
    format: str = ib(default="wav")
    escape_digits: str = ib(default="#")
    timeout: int = ib(default=20000)
    offset: int = ib(default=0)
    beep: str = ib(default="beep")
    silence: int = ib(default=None)
    o_connection: str = ib(default="")
