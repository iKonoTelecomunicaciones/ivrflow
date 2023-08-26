from .base import Base
from typing import Dict
from repository.nodes import Playback as PlaybackModel


class Playback(Base):
    def __init__(self, default_variables: Dict, playback_content: PlaybackModel) -> None:
        super().__init__(default_variables)
        self.content = playback_content

    async def run(self) -> None:
        self.log.debug(f"Running playback node {self.id}")
        self.log.debug(f"Playback node {self.id} finished")
        return
