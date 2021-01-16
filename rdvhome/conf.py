

from rpy.functions.datastructures import data

import asyncio

loop = asyncio.get_event_loop()

settings = data(
    DEBUG=False,
    SERVER_PORT=8500,
    SERVER_ADDRESS="0.0.0.0",
    SWITCHES={},
    CONTROLS={},
    DEPENDENCIES={
        "aiohttp": "3.7.3",
        "aiofiles": "0.3.2",
        # "fabric3": "1.13.1.post1",
        #'hap-python': None,
        "aiohttp-autoreload": "0.0.1",
        "aioreactive": "0.5.0",
        "asyncio": "3.4.3",
        "colour": "0.1.5",
        "django": None,
        "six": None,
        "yarl": "1.6.3",
        "base36": "0.1.1",
        "pyqrcode": None,
        "hap-python": "2.8.4",
        "python-rpy": "1.0.17",
        "websockets": "8.1",
        "zeroconf": "0.26.3",
        "gpioserver": "1.0.4",
    },
)