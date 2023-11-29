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
        text: "Please enter your account number"
        file: "vm-exten"
        # This is the sound file that will be played to the user while the ASR is executed
        progress_sound: "custom/progress"
        middlewares:
            tts:
                text: "Please enter your account number"
            asr:
                prompt_file: "{{ tts_azure.file }}"
                progress_sound: "custom/progress"
                record_path_variable: "asr_file_path"
        timeout: 5
        max_digits: 1
        dtmf_input: opt
        validation: '{{ opt }}'
        cases:
        - id: 1
            o_connection: hello
        - id: default
            o_connection: monkey

    ```
    """

    file: str = ib(factory=str)
    middlewares: Dict = ib(default=None)
    timeout: int = ib(factory=int)
    max_digits: int = ib(factory=int)
    dtmf_input: str = ib(factory=str)

    @classmethod
    def from_dict(cls, node: Dict) -> "GetData":
        return cls(
            id=node.get("id"),
            type=node.get("type"),
            file=node.get("file"),
            middlewares=node.get("middlewares"),
            timeout=node.get("timeout", 5000),
            max_digits=node.get("max_digits", 255),
            dtmf_input=node.get("dtmf_input"),
            validation=node.get("validation"),
            cases=[Case(**case) for case in node.get("cases", [])],
        )
