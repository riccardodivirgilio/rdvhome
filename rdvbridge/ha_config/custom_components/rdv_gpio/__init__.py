"""RDV GPIO Lights - pulse-toggle relay control for Home Assistant."""
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

DOMAIN = "rdv_gpio"

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True
