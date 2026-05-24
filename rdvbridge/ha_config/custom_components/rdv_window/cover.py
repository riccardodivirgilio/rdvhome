"""GPIO motor window cover platform.

Two relays: power (active-LOW, HIGH=off) and direction (HIGH=up, LOW=down).
Always set direction with power HIGH (motor stopped) before energising power.
Auto-stops after TIMING_UP / TIMING_DOWN seconds via a cancellable asyncio task.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.cover import (
    PLATFORM_SCHEMA,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.const import CONF_NAME, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

CONF_GPIO_POWER = "gpio_power"
CONF_GPIO_DIRECTION = "gpio_direction"
TIMING_UP = 13    # seconds to fully open
TIMING_DOWN = 12  # seconds to fully close

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_GPIO_POWER): cv.positive_int,
    vol.Required(CONF_GPIO_DIRECTION): cv.positive_int,
    vol.Optional(CONF_UNIQUE_ID): cv.string,
})


def _setup_gpio():
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    return GPIO


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    try:
        gpio = await hass.async_add_executor_job(_setup_gpio)
    except Exception as err:
        _LOGGER.error("Failed to initialise GPIO: %s", err)
        return

    cover = GpioWindowCover(
        name=config[CONF_NAME],
        gpio_power=config[CONF_GPIO_POWER],
        gpio_direction=config[CONF_GPIO_DIRECTION],
        unique_id=config.get(CONF_UNIQUE_ID),
        gpio=gpio,
    )
    await hass.async_add_executor_job(cover.init_gpio)
    async_add_entities([cover])


class GpioWindowCover(CoverEntity):
    _attr_should_poll = False
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    def __init__(
        self,
        name: str,
        gpio_power: int,
        gpio_direction: int,
        unique_id: str | None,
        gpio,
    ) -> None:
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._gpio_power = gpio_power
        self._gpio_direction = gpio_direction
        self._gpio = gpio
        self._is_opening = False
        self._is_closing = False
        self._stop_task: asyncio.Task | None = None

    def init_gpio(self) -> None:
        self._gpio.setup(self._gpio_power, self._gpio.OUT, initial=self._gpio.HIGH)
        self._gpio.setup(self._gpio_direction, self._gpio.OUT, initial=self._gpio.HIGH)

    @property
    def is_closed(self) -> bool | None:
        return None  # no position sensor — state is opening/closing/unknown

    @property
    def is_opening(self) -> bool:
        return self._is_opening

    @property
    def is_closing(self) -> bool:
        return self._is_closing

    # --- GPIO helpers (blocking, run in executor) ---

    def _gpio_stop(self) -> None:
        self._gpio.output(self._gpio_power, self._gpio.HIGH)
        self._gpio.output(self._gpio_direction, self._gpio.HIGH)

    def _gpio_start_up(self) -> None:
        self._gpio.output(self._gpio_power, self._gpio.HIGH)        # ensure stopped first
        self._gpio.output(self._gpio_direction, self._gpio.HIGH)    # direction = up
        self._gpio.output(self._gpio_power, self._gpio.LOW)         # energise

    def _gpio_start_down(self) -> None:
        self._gpio.output(self._gpio_power, self._gpio.HIGH)        # ensure stopped first
        self._gpio.output(self._gpio_direction, self._gpio.LOW)     # direction = down
        self._gpio.output(self._gpio_power, self._gpio.LOW)         # energise

    # --- timer ---

    def _cancel_stop(self) -> None:
        if self._stop_task and not self._stop_task.done():
            self._stop_task.cancel()
        self._stop_task = None

    async def _auto_stop(self, seconds: float) -> None:
        try:
            await asyncio.sleep(seconds)
        except asyncio.CancelledError:
            return
        await self.hass.async_add_executor_job(self._gpio_stop)
        self._is_opening = False
        self._is_closing = False
        self.async_write_ha_state()

    # --- cover actions ---

    async def async_open_cover(self, **kwargs: Any) -> None:
        self._cancel_stop()
        await self.hass.async_add_executor_job(self._gpio_start_up)
        self._is_opening = True
        self._is_closing = False
        self._stop_task = self.hass.async_create_task(self._auto_stop(TIMING_UP))
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs: Any) -> None:
        self._cancel_stop()
        await self.hass.async_add_executor_job(self._gpio_start_down)
        self._is_opening = False
        self._is_closing = True
        self._stop_task = self.hass.async_create_task(self._auto_stop(TIMING_DOWN))
        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        self._cancel_stop()
        await self.hass.async_add_executor_job(self._gpio_stop)
        self._is_opening = False
        self._is_closing = False
        self.async_write_ha_state()
