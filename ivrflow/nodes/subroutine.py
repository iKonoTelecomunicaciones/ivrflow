import json
from queue import LifoQueue
from typing import Dict

from ..channel import Channel
from ..db.channel import ChannelState
from ..models import Subroutine as SubroutineModel
from .base import Base


class Subroutine(Base):
    """This class is used to handle the subroutine node."""

    def __init__(
        self, subroutine_node_data: SubroutineModel, channel: Channel, default_variables: Dict
    ) -> None:
        Base.__init__(self, channel=channel, default_variables=default_variables)
        self.log = self.log.getChild(subroutine_node_data.id)
        self.content: SubroutineModel = subroutine_node_data

    @property
    def go_sub(self) -> str:
        return self.render_data(self.content.go_sub)

    async def run(self):
        """This function runs the subroutine node."""
        self.log.info(f"Channel {self.channel.channel_uniqueid} enters subroutine node {self.id}")

        # Get current stack data
        lifo_stack: LifoQueue = self.channel._stack
        stack: Dict = json.loads(self.channel.stack)
        last_node = None

        try:
            go_sub = self.go_sub
            if not go_sub:
                self.log.warning(
                    f"The go_sub value in {self.id} not found. Please check the configuration"
                )
                return

            # If the stack is empty, add the current node to the stack
            if lifo_stack.empty():
                self.log.info(f"Add '{self.id}' node to empty LiFo Stack")
                lifo_stack.put(self.id)
            else:
                # Get the last node from the stack
                last_node = lifo_stack.get(timeout=3)  # seconds

                # If this node is not the last node, add it to the stack
                if last_node and last_node != self.id:
                    self.log.info(f"Add '{self.id}' node to LiFo Stack: {lifo_stack.queue}")
                    lifo_stack.put(self.id)

            # Update the stack in db
            stack[self.channel.channel_uniqueid] = lifo_stack.queue
            self.channel.stack = json.dumps(stack)
            await self.channel.update()
        except ValueError as e:
            self.log.warning(e)

        # Update the menu
        if not lifo_stack.empty() and last_node != self.id:
            self.log.debug(f"Go to subroutine: '{self.go_sub}'")
            await self.channel.update_ivr(node_id=self.go_sub)

        # If the stack is empty, o finished subroutine go to the next node
        o_connection = self.render_data(self.content.o_connection)
        if lifo_stack.empty() or last_node == self.id:
            self.log.debug(f"Go to next node: '{o_connection}'")
            await self.channel.update_ivr(
                node_id=o_connection,
                state=ChannelState.END if not o_connection else None,
            )
