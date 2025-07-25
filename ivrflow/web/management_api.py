from __future__ import annotations

import logging
from typing import Dict

import aiohttp_cors
from aiohttp import web
from aiohttp_swagger3 import SwaggerDocs, SwaggerInfo, SwaggerUiSettings
from mautrix.util.logging import TraceLogger

from .. import VERSION
from ..config import config
from ..flow_utils import FlowUtils
from . import api
from .base import routes, set_config


class ManagementAPI:
    """Management API base class"""

    log: TraceLogger = logging.getLogger("ivrflow.management_api")
    app: web.Application

    def __init__(self, flow_utils: FlowUtils) -> None:
        self.app = web.Application()
        set_config(config=config, flow_utils=flow_utils)

        swagger = SwaggerDocs(
            self.app,
            info=SwaggerInfo(
                title="IVRFlow API",
                description=(
                    "Documentation for IVRFlow asterisk IVR builder "
                    "project by **iKono Telecomunicaciones S.A.S.**"
                ),
                version=f"v{VERSION}",
            ),
            components="ivrflow/web/api/components.yaml",
            swagger_ui_settings=SwaggerUiSettings(
                path="/docs",
                layout="BaseLayout",
            ),
        )

        swagger.add_routes(routes)

        cors = aiohttp_cors.setup(
            self.app,
            defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods=["GET", "POST", "OPTIONS", "PATCH", "DELETE"],
                )
            },
        )

        for route in list(self.app.router.routes()):
            cors.add(route)
            if route.method in ["post", "POST"]:
                route_info: Dict = route.get_info()
                if route_info.get("path") not in self._get_registered_options_paths():
                    swagger.add_options(
                        path=route_info.get("path") or route_info.get("formatter"),
                        handler=self.options,
                    )

    @property
    def _acao_headers(self) -> dict[str, str]:
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PATCH, DELETE",
        }

    @property
    def _headers(self) -> dict[str, str]:
        return {**self._acao_headers, "Content-Type": "application/json"}

    async def options(self, _: web.Request):
        return web.Response(status=200, headers=self._headers)

    def _get_registered_options_paths(self) -> set[str]:
        return {
            r.get_info().get("path") or r.get_info().get("formatter")
            for r in self.app.router.routes()
            if r.method == "OPTIONS"
        }
