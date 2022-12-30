"""The Luxtronik heatpump integration."""
# region Imports
from dataclasses import dataclass
from typing import Final

from luxtronik import Luxtronik

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription

from .const import DOMAIN
from .coordinator import LuxtronikCoordinator

# endregion Imports

PLATFORMS: Final[list[Platform]] = [
    Platform.SWITCH,
]


@dataclass
class LuxtronikEntityDescription(EntityDescription):
    """Class describing Luxtronik entities."""

    luxtronik_key: str = ""


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    host = config_entry.data[CONF_HOST]
    port = config_entry.data[CONF_PORT]

    client = Luxtronik(host=host, port=port, safe=False)
    coordinator = LuxtronikCoordinator(
        hass=hass,
        client=client,
        config=config_entry.data,
    )

    # lang = hass.config.language

    await coordinator.async_config_entry_first_refresh()
    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))

    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    # Trigger a refresh again now that all platforms have registered
    hass.async_create_task(coordinator.async_refresh())
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    ):
        coordinator: LuxtronikCoordinator = hass.data[DOMAIN].pop(config_entry.entry_id)
        await coordinator.async_shutdown()

    return unload_ok


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)
