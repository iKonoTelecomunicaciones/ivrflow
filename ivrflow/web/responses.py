from __future__ import annotations

from http import HTTPStatus
from typing import Dict, Optional

from aiohttp import web


def json_response(
    status: HTTPStatus, message: Optional[str] = None, data: Optional[Dict] = None
) -> web.Response:
    if message:
        response = {"detail": {"message": message}}
        if data:
            response["detail"]["data"] = data
    else:
        response = data

    return web.json_response(response, status=status)
