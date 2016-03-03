# -*- coding: utf-8 -*-

from aiohttp.web import Application, run_app

from aiohttp_wsgi import WSGIHandler

from rdvhome.wsgi import application

aiohttp_application = Application()
wsgi_handler = WSGIHandler(application)
aiohttp_application.router.add_route("*", "/{path_info:.*}", wsgi_handler.handle_request)

run_app(aiohttp_application)