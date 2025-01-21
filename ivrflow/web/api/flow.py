from aiohttp import web

from .. import routes


@routes.get("/hello-flow")
async def hello_flow(request):
    return web.json_response({"hello": "flow"})
