from __future__ import annotations

import json
from logging import getLogger
from typing import Any, Dict, cast

from mautrix.util.logging import TraceLogger

from .config import Config
from .db.channel import Channel as DBChannel
from .db.channel import ChannelState
from .types import ChannelUniqueID


class Channel(DBChannel):
    by_channel_uniqueid: Dict[ChannelUniqueID, "Channel"] = {}

    config: Config
    log: TraceLogger = getLogger("ivrflow.channel")

    def __init__(
        self,
        channel_uniqueid: ChannelUniqueID,
        node_id: str,
        state: ChannelState = None,
        id: int = None,
        variables: str = "{}",
    ) -> None:
        self._variables: Dict = json.loads(variables)
        super().__init__(
            id=id,
            channel_uniqueid=channel_uniqueid,
            node_id=node_id,
            state=state,
            variables=f"{variables}",
        )
        self.log = self.log.getChild(self.channel_uniqueid)

    def _add_to_cache(self) -> None:
        if self.channel_uniqueid:
            self.by_channel_uniqueid[self.channel_uniqueid] = self

    async def clean_up(self):
        del self.by_channel_uniqueid[self.channel_uniqueid]
        self.variables = "{}"
        self._variables = {}
        self.node_id = "start"
        self.state = None
        await self.update()

    @classmethod
    async def get_by_channel_uniqueid(
        cls, channel_uniqueid: ChannelUniqueID, create: bool = True
    ) -> "Channel" | None:
        """It gets a channel from the database, or creates one if it doesn't exist

        Parameters
        ----------
        channel_uniqueid : ChannelUniqueID
            The channel_uiniqueid.
        create : bool, optional
            If True, the channel will be created if it doesn't exist.

        Returns
        -------
            The channel object

        """
        try:
            return cls.by_channel_uniqueid[channel_uniqueid]
        except KeyError:
            pass

        channel = cast(cls, await super().get_by_channel_uniqueid(channel_uniqueid))

        if channel is not None:
            channel._add_to_cache()
            return channel

        if create:
            channel = cls(channel_uniqueid=channel_uniqueid, node_id="start")
            await channel.insert()
            channel = cast(cls, await super().get_by_channel_uniqueid(channel_uniqueid))
            channel._add_to_cache()
            return channel

    async def get_variable(self, variable_id: str) -> Any | None:
        """This function returns the value of a variable with the given ID

        Parameters
        ----------
        variable_id : str
            The id of the variable you want to get.

        Returns
        -------
            The value of the variable with the given id.

        """
        return self._variables.get(variable_id)

    async def set_variable(self, variable_id: str, value: Any):
        if not variable_id:
            return

        self._variables[variable_id] = value
        self.variables = json.dumps(self._variables)
        self.log.debug(
            f"Saving variable [{variable_id}] to channel "
            "[{self.channel_uniqueid}] :: content [{value}]"
        )
        await self.update()

    async def set_variables(self, variables: Dict):
        """It takes a dictionary of variable IDs and values, and sets the variables to the values

        Parameters
        ----------
        variables : Dict
            A dictionary of variable names and values.

        """
        for variable in variables:
            await self.set_variable(variable_id=variable, value=variables[variable])

    async def update_ivr(self, node_id: str | ChannelState, state: ChannelState = None):
        """Updates the IVR's node_id and state, and then updates the IVR's content

        Parameters
        ----------
        node_id : str
            The node_id of the IVR. This is used to determine which IVR to display.
        state : str
            The state of the IVR. This is used to determine which IVR to display.

        """
        self.log.debug(
            f"The [channel: {self.channel_uniqueid}] will update his [node: {self.node_id}] to"
            f"[{node_id.value if isinstance(node_id, ChannelState) else node_id}] "
            f"and his [state: {self.state}] to [{state}]"
        )
        self.node_id = node_id.value if isinstance(node_id, ChannelState) else node_id
        self.state = state
        await self.update()
        self._add_to_cache()
