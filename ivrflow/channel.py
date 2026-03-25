from __future__ import annotations

import json
from logging import getLogger
from typing import Any, Dict, List, cast

from glom import Delete, PathAccessError, assign, glom
from mautrix.util.logging import TraceLogger

from .config import Config
from .db.channel import Channel as DBChannel
from .db.channel import ChannelState
from .scope import Scope
from .types import ChannelUniqueID
from .utils.jq2glom import JQ2Glom
from .utils.util import Util


class Channel(DBChannel):
    by_channel_uniqueid: Dict[ChannelUniqueID, "Channel"] = {}

    config: Config
    log: TraceLogger = getLogger("ivrflow.channel")

    # JQ2Glom instance
    _jq2glom: JQ2Glom = JQ2Glom()

    def __init__(
        self,
        channel_uniqueid: ChannelUniqueID,
        node_id: str,
        state: ChannelState = None,
        id: int = None,
        variables: str = "{}",
        stack: str = "{}",
    ) -> None:
        super().__init__(
            id=id,
            channel_uniqueid=channel_uniqueid,
            node_id=node_id,
            state=state,
            variables=f"{variables}",
            stack=stack,
        )
        self.log = self.log.getChild(self.channel_uniqueid)

    def _add_to_cache(self) -> None:
        if self.channel_uniqueid:
            self.by_channel_uniqueid[self.channel_uniqueid] = self

    async def clean_up(self) -> None:
        del self.by_channel_uniqueid[self.channel_uniqueid]
        self.variables = "{}"
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

        channel: Channel | None = cast(
            cls, await super().get_by_channel_uniqueid(channel_uniqueid)
        )

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

        scope, key = Util.get_scope_and_key(variable_id)

        try:
            _value = glom(self._variables, self._jq2glom.to_glom_path(f"{scope.value}.{key}"))
            self.log.debug(
                f"[{self.channel_uniqueid}] [VAR][GET] {scope.value}.{key} => {repr(_value)}"
            )
            return _value
        except PathAccessError as e:
            self.log.debug(
                f"[{self.channel_uniqueid}] [VAR][GET] {scope.value}.{key} => Not found"
            )
            return
        except Exception as e:
            self.log.error(f"[{self.channel_uniqueid}] [VAR][GET] {scope.value}.{key} => {e}")
            return

    async def set_variable(self, variable_id: str, value: Any) -> None:
        """
        The function sets a variable with a given ID and value, updates the variables dictionary.

        Parameters
        ----------
        variable_id : str
            The `variable_id` parameter is a string that represents
            the unique identifier of the variable you want to set.
        value : Any
            The `value` parameter in the `set_variable` function is the value
            that you want to assign to the variable identified by `variable_id`.
            It can be of any data type (e.g., string, integer, boolean, etc.).

        Returns
        -------
            None

        """

        if not variable_id:
            return

        scope, key = Util.get_scope_and_key(variable_id)
        if not key:
            self.log.error(
                f"[{self.channel_uniqueid}] [VAR][SET] Invalid variable id (empty key): {variable_id!r}"
            )
            return

        try:
            entry = Scope(channel=self).resolve(scope)
        except Exception as e:
            self.log.error(str(e))
            return

        variables = entry.get_scope_vars()

        try:
            assign(variables, self._jq2glom.to_glom_path(key), value, missing=dict)
            self.log.debug(
                f"[{self.channel_uniqueid}] [VAR][SET] {scope.value}.{key} = {repr(value)}"
            )
        except Exception as e:
            self.log.error(f"[{self.channel_uniqueid}] [VAR][SET] {scope.value}.{key} => {e}")
            return

        await entry.update()

    async def set_variables(self, variables: Dict) -> None:
        """It takes a dictionary of variable IDs and values, and sets the variables to the values

        Parameters
        ----------
        variables : Dict
            A dictionary of variable names and values.

        """
        for variable in variables:
            await self.set_variable(variable_id=variable, value=variables[variable])

    async def update_ivr(self, node_id: str | ChannelState, state: ChannelState = None) -> None:
        """Updates the IVR's node_id and state, and then updates the IVR's content

        Parameters
        ----------
        node_id : str
            The node_id of the IVR. This is used to determine which IVR to display.
        state : str
            The state of the IVR. This is used to determine which IVR to display.

        """

        _node_id = node_id.value if isinstance(node_id, ChannelState) else node_id

        self.log.debug(
            f"[{self.channel_uniqueid}] will be updated. "
            f"Node: ([{self.node_id}] => [{_node_id}]) "
            f"State: ([{self.state}] => [{state}])"
        )
        self.node_id = _node_id
        self.state = state
        await self.update()
        self._add_to_cache()

    async def del_variables(self, variables: List = []) -> None:
        """This function delete the variables in the channel

        Parameters
        ----------
            variables: List
                The variables to delete.
        """
        for variable in variables:
            await self.del_variable(variable_id=variable)

    async def del_variable(self, variable_id: str) -> None:
        """The function delete a variable in either the channel and updates the corresponding JSON data.

        Parameters
        ----------
        variable_id : str
            The `variable_id` parameter is a string that represents the identifier of the variable you want to set.
        """
        if not variable_id:
            return

        scope, key = Util.get_scope_and_key(variable_id)

        try:
            entry = Scope(channel=self).resolve(scope)
        except Exception as e:
            self.log.error(str(e))
            return

        variables = entry.get_scope_vars()
        if not variables:
            self.log.debug(f"[{self.channel_uniqueid}] Variables in scope {scope.value} are empty")
            return

        try:
            glom(variables, Delete(self._jq2glom.to_glom_path(key)))
            self.log.debug(f"[{self.channel_uniqueid}] [VAR][DEL] {scope.value}.{key} => Deleted")
        except PathAccessError as e:
            self.log.debug(
                f"[{self.channel_uniqueid}] [VAR][DEL] {scope.value}.{key} => Not found"
            )
            return
        except Exception as e:
            self.log.error(f"[{self.channel_uniqueid}] [VAR][DEL] {scope.value}.{key} => {e}")
            return

        await entry.update()
