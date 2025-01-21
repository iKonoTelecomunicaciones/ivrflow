from aiohttp import web

from ..base import routes


@routes.get("/hello-flow")
async def hello_flow(request):
    return web.json_response({"hello": "flow"})
