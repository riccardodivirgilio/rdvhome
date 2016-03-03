
from aiohttp import web

async def hello(request):
    return web.json_response({"success": True})

app = web.Application()
app.router.add_route('*', '/', hello)

web.run_app(app)