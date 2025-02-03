from __future__ import annotations

from typing import List

from attr import dataclass, ib

from ..flow_object import FlowObject


@dataclass
class Email(FlowObject):
    """
    ## Email

    A email node allows a email to be sent,
    these emails can be formatted using jinja variables.

    content:

    ```
    - id: m1
      type: email
      server_id: "sample-server-id"
      subject: The subject
      recipients:
        - foo1@foo.com
        - foo2@foo.com
        - foo2@foo.com
      attachments:
        - https://www.w3.org/People/mimasa/test/imgformat/img/w3c_home.png
        - https://www.gstatic.com/webp/gallery/1.jpg
        - https://www.orimi.com/pdf-test.pdf
        - https://samplelib.com/lib/preview/mp4/sample-5s.mp4
      text: "Hello World!"
      format: "html"
      encode_type: "utf-8"
      o_connection: m2
    ```
    """

    text: str = ib(default=None)
    server_id: str = ib(default=None)
    subject: str = ib(default=None)
    recipients: List[str] = ib(default=None)
    attachments: List[str] = ib(default=None)
    format: str = ib(default=None)
    encode_type: str = ib(default=None)
    o_connection: str = ib(default=None)

    @staticmethod
    def from_dict(node: dict) -> Email:
        return Email(
            id=node.get("id"),
            type=node.get("type"),
            text=node.get("text"),
            server_id=node.get("server_id"),
            subject=node.get("subject"),
            recipients=node.get("recipients"),
            attachments=node.get("attachments"),
            format=node.get("format"),
            encode_type=node.get("encode_type"),
            o_connection=node.get("o_connection"),
        )
