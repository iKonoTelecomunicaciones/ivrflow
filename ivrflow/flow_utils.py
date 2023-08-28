from __future__ import annotations

import logging
from typing import Dict

from mautrix.util.logging import TraceLogger

from .middlewares.http import HTTPMiddleware
from .repository import FlowUtils as FlowUtilsModel
from .repository.middlewares.http import HTTPMiddleware as HTTPMiddlewareModel

log: TraceLogger = logging.getLogger("ivrflow.flow_utils")


class FlowUtils:
    # Cache dicts
    middlewares_by_id: Dict[str, HTTPMiddlewareModel] = {}

    def __init__(self) -> None:
        self.data: FlowUtilsModel = FlowUtilsModel.load_flow_utils()

    def _add_middleware_to_cache(self, middleware_model: HTTPMiddlewareModel):
        self.middlewares_by_id[middleware_model.id] = middleware_model

    def get_middleware_by_id(self, middleware_id: str) -> HTTPMiddleware | None:
        """This function retrieves a middleware by its ID from a cache or a list of middlewares.

        Parameters
        ----------
        middleware_id : str
            A string representing the ID of the middleware that needs to be retrieved.

        Returns
        -------
            This function returns a dictionary object representing a middleware in a graph, or `None`
            if the node with the given ID is not found.

        """

        try:
            return self.middlewares_by_id[middleware_id]
        except KeyError:
            pass

        try:
            for middleware in self.data.middlewares:
                if middleware_id == middleware.get("id", ""):
                    http_middleware = HTTPMiddlewareModel(**middleware)
                    self._add_middleware_to_cache(http_middleware)
                    return http_middleware
        except AttributeError:
            log.warning("No middlewares found in flow_utils.json")
