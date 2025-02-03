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
      file: "tt-monkeys"
      scape_digits: "1234567890*#"
      sample_offset: 1000
      o_connection: m2

    - id: m2
      type: playback
      middlweware:
        tts:
          text: Hello, this is a test with TTS
          exten: "wav"
          file_type: "wav"
          voice_name: "es-MX-JorgeNeural"
          provider: "azure"
      file: "{{ tts.file }}"
      scape_digits: "1234567890*#"
      sample_offset: 1000
      o_connection: m3
    ```
    """

    file: str = ib(default="")
    middleware: Dict = ib(default=None)
    escape_digits: str = ib(default="")
    sample_offset: int = ib(default=0)
    o_connection: str = ib(default="")

    @staticmethod
    def from_dict(node: Dict) -> "Playback":
        return Playback(
            id=node.get("id"),
            type=node.get("type"),
            file=node.get("file"),
            middleware=node.get("middleware"),
            escape_digits=node.get("scape_digits"),
            sample_offset=node.get("sample_offset"),
            o_connection=node.get("o_connection"),
        )
