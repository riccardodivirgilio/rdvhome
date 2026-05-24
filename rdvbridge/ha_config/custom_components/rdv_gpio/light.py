"""GPIO pulse-toggle relay light platform."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import voluptuous as vol

from homeassistant.components.light import PLATFORM_SCHEMA, LightEntity, ColorMode
from homeassistant.const import CONF_NAME, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)

CONF_GPIO_RELAY = "gpio_relay"
CONF_GPIO_STATUS = "gpio_status"
PULSE_DURATION = 0.025  # 25ms pulse
DEBOUNCE_SECONDS = 1.0

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_GPIO_RELAY): cv.positive_int,
    vol.Optional(CONF_GPIO_STATUS): cv.positive_int,
    vol.Optional(CONF_UNIQUE_ID): cv.string,
})


def setup_gpio():
    """Set up RPi.GPIO in BCM mode."""
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
        gpio = await hass.async_add_executor_job(setup_gpio)
    except Exception as err:
        _LOGGER.error("Failed to initialise GPIO: %s", err)
        return

    light = GpioRelayLight(
        name=config[CONF_NAME],
        gpio_relay=config[CONF_GPIO_RELAY],
        gpio_status=config.get(CONF_GPIO_STATUS),
        unique_id=config.get(CONF_UNIQUE_ID),
        gpio=gpio,
    )

    await hass.async_add_executor_job(light.init_gpio)
    async_add_entities([light])


class GpioRelayLight(LightEntity):
    """A light backed by a pulse-toggle GPIO relay with optional status input."""

    _attr_should_poll = True
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, name: str, gpio_relay: int, gpio_status: int | None,
                 unique_id: str | None, gpio) -> None:
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._gpio_relay = gpio_relay
        self._gpio_status = gpio_status
        self._gpio = gpio
        self._is_on = False
        self._last_pulse = 0.0

    def init_gpio(self) -> None:
        self._gpio.setup(self._gpio_relay, self._gpio.OUT, initial=self._gpio.HIGH)
        if self._gpio_status is not None:
            self._gpio.setup(self._gpio_status, self._gpio.IN, pull_up_down=self._gpio.PUD_UP)
            # Read initial state
            self._is_on = not bool(self._gpio.input(self._gpio_status))

    @property
    def is_on(self) -> bool:
        return self._is_on

    def _pulse(self) -> None:
        now = time.monotonic()
        if now - self._last_pulse < DEBOUNCE_SECONDS:
            return
        self._last_pulse = now
        self._gpio.output(self._gpio_relay, self._gpio.LOW)
        time.sleep(PULSE_DURATION)
        self._gpio.output(self._gpio_relay, self._gpio.HIGH)

    def turn_on(self, **kwargs: Any) -> None:
        if not self._is_on:
            self._pulse()
            self._is_on = True

    def turn_off(self, **kwargs: Any) -> None:
        if self._is_on:
            self._pulse()
            self._is_on = False

    def update(self) -> None:
        """Read physical switch state from GPIO status pin."""
        if self._gpio_status is not None:
            self._is_on = not bool(self._gpio.input(self._gpio_status))
