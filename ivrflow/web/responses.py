from __future__ import annotations

from http import HTTPStatus
from logging import DEBUG, Logger, getLogger
from typing import Dict, Optional

from aiohttp import web

log: Logger = getLogger("ivrflow.api.responses")

MESSAGES = {
    "body_not_json": "Request body is not JSON",
}


class _Response:
    @staticmethod
    def base_response(
        status: HTTPStatus,
        message: str,
        uuid: str = "",
        data: dict | None = None,
    ) -> web.Response:

        if message:
            log.info(f"({uuid}) -> {message}" if uuid else message)
            response = {"detail": {"message": message}}
            if data:
                response["detail"]["data"] = data
        else:
            log.info(f"({uuid}) -> {data}" if uuid else data)
            response = data

        return web.json_response(response, status=status)

    @classmethod
    def bad_request(cls, message: str, uuid: str = "", data: dict = None) -> web.Response:
        return cls.base_response(HTTPStatus.BAD_REQUEST, message, uuid, data)

    @classmethod
    def not_found(cls, message: str, uuid: str = "") -> web.Response:
        return cls.base_response(HTTPStatus.NOT_FOUND, message, uuid)

    @classmethod
    def internal_error(
        cls, error: Exception, uuid: str = "", logger: Logger = DEBUG
    ) -> web.Response:
        if logger.getEffectiveLevel() <= DEBUG:
            logger.exception(f"({uuid}) -> Error: {error}")
        return cls.base_response(HTTPStatus.INTERNAL_SERVER_ERROR, str(error), uuid)

    @classmethod
    def success_response(cls, message: str, uuid: str = "", data: dict = None) -> web.Response:
        return cls.base_response(HTTPStatus.OK, message, uuid, data)

    @classmethod
    def created(cls, message: str, uuid: str = "", data: dict = None) -> web.Response:
        return cls.base_response(HTTPStatus.CREATED, message, uuid, data)

    # Personalized responses
    @classmethod
    def body_not_json(cls, uuid: str = "") -> web.Response:
        return cls.bad_request(MESSAGES["body_not_json"], uuid)


resp = _Response()


# TODO: Remove this function when all responses are migrated to _Response
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
