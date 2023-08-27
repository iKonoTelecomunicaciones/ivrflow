from __future__ import annotations

import logging
from typing import Dict

from mautrix.util.logging import TraceLogger

from .channel import Channel
from .nodes import Playback, Switch
from .repository import Flow as FlowModel


class Flow:
    log: TraceLogger = logging.getLogger("ivrflow.flow")

    nodes: Dict[str, object]
    nodes_by_id: Dict[str, object] = {}

    def __init__(self, *, flow_data: FlowModel) -> None:
        self.content: FlowModel = flow_data
        self.nodes = self.content.nodes

    def _add_node_to_cache(self, node_data: Playback):
        self.nodes_by_id[node_data.id] = node_data

    @property
    def flow_variables(self) -> Dict:
        return self.content.flow_variables

    def get_node_by_id(self, node_id: str) -> Dict | None:
        """This function returns a node from a cache or a list of nodes based on its ID.

        Parameters
        ----------
        node_id : str
            The ID of the node that we want to retrieve from the graph.

        Returns
        -------
            This function returns a dictionary object representing a node in a graph, or `None`
            if the node with the given ID is not found.

        """

        try:
            return self.nodes_by_id[node_id]
        except KeyError:
            pass

        for node in self.nodes:
            if node_id == node.id:
                self._add_node_to_cache(node)
                return node

    def node(self, channel: Channel) -> Playback | Switch | None:
        node_data = self.get_node_by_id(node_id=channel.node_id)

        if not node_data:
            return

        if node_data.type == "playback":
            node_initialized = Playback(
                playback_content=node_data, default_variables=self.flow_variables, channel=channel
            )
        elif node_data.type == "switch":
            node_initialized = Switch(
                switch_content=node_data, default_variables=self.flow_variables, channel=channel
            )
        else:
            return

        return node_initialized
