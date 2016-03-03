
from aiohttp import web
import asyncio

@asyncio.coroutine
def hello(request):
    return web.json_response({"success": True, "message": "OK"})

app = web.Application()
app.router.add_route('*', '/', hello)

web.run_app(app)