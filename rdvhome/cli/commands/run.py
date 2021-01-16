

from aiohttp import web

from rdvhome.app import app
from rdvhome.conf import settings
from rdvhome.state import controllers, switches
from rdvhome.utils.json import dumps

from rpy.cli.utils import SimpleCommand
from rpy.functions.asyncio import run_all
from rpy.functions.importutils import module_path
from rpy.functions.process import system_open

async def log(event):
    print(
        event.id, event.get("on", None) and "on" or "off", event.get("color", None) or "",
    )

class Command(SimpleCommand):

    help = "Run the home app"

    def add_arguments(self, parser):
        parser.add_argument("--open", dest="auto_open", default=False, action="store_true")

    def handle(
        self, port=settings.SERVER_PORT, address=settings.SERVER_ADDRESS, auto_open=False,
    ):

        if settings.DEBUG:
            import aiohttp_autoreload

            aiohttp_autoreload.start()

            with open(
                module_path("rdvhome", "frontend", "src", "data", "switches.js"), "wb"
            ) as f:

                data = "export default %s" % dumps(
                    {
                        s.id: dict(
                            id=s.id,
                            name=s.name,
                            icon=s.icon,
                            ordering=s.ordering,
                            allow_visibility=s.visible,
                        )
                        for s in switches
                    },
                    indent=4,
                )

                f.write(data.encode("utf-8"))

        run_all(
            # switches.subscribe(log),
            (switches.watch(), switches.start(), controllers.watch(), controllers.start(),)
        )

        if auto_open:
            system_open("http://%s:%s" % (address, port))

        # We want SIGTERM (kill) to be handled by the driver itself,
        # so that it can gracefully stop the accessory, server and advertising.
        # from rdvhome.homekit import driver
        # signal.signal(signal.SIGTERM, driver.signal_handler)

        # code borrowed from pyhap
        try:
            # driver.add_job(driver._do_start)
            # print("TO CONNECT TO HOMEKIT USE: %s" % driver.state.pincode.decode())
            web.run_app(app, port=port)
        except KeyboardInterrupt:
            driver.loop.call_soon_threadsafe(driver.loop.create_task, driver.async_stop())
            driver.loop.run_forever()
        finally:
            driver.loop.close()