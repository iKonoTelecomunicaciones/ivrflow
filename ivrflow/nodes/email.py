import asyncio
from typing import Dict, List

from ..channel import Channel, ChannelState
from ..email_client import Email as EmailMessage
from ..email_client import EmailClient
from ..models import Email as EmailModel
from .base import Base


class Email(Base):
    email_client: EmailClient = None

    def __init__(
        self, default_variables: Dict, email_content: EmailModel, channel: Channel
    ) -> None:
        super().__init__(default_variables, channel=channel)
        self.log = self.log.getChild(email_content.id)
        self.content: EmailModel = email_content

    @property
    def server_id(self) -> str:
        return self.render_data(self.content.get("server_id", ""))

    @property
    def subject(self) -> str:
        return self.render_data(self.content.get("subject", ""))

    @property
    def recipients(self) -> List[str]:
        return self.render_data(self.content.get("recipients", []))

    @property
    def attachments(self) -> List[str]:
        return self.render_data(self.content.get("attachments", []))

    @property
    def format(self) -> str:
        return self.render_data(self.content.get("format", ""))

    @property
    def encode_type(self) -> str:
        return self.render_data(self.content.get("encode_type", ""))

    @property
    def text(self):
        return self.render_data(data=self.content.text)

    @property
    def o_connection(self) -> str:
        return self.get_o_connection()

    async def _update_node(self):
        await self.channel.update_ivr(
            node_id=self.o_connection,
            state=ChannelState.END if not self.o_connection else None,
        )

    async def run(self):
        self.log.info(f"[{self.channel.channel_uniqueid}] Entering email node {self.id}")
        if not self.email_client:
            self.email_client = EmailClient.get_by_server_id(self.server_id)

        self.log.debug(
            f"[{self.channel.channel_uniqueid}] Sending email {self.subject or self.text} to {self.recipients}"
        )

        email = EmailMessage(
            subject=self.subject,
            text=self.text,
            recipients=self.recipients,
            attachments=self.attachments,
            format=self.format,
            encode_type=self.encode_type,
        )

        asyncio.create_task(self.email_client.send_email(email=email))

        await self._update_node()
