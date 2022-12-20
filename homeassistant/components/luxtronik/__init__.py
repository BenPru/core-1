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
        # config=config_entry.data,
    )
    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))

    await coordinator.async_config_entry_first_refresh()

    data = hass.data.setdefault(DOMAIN, {})
    data[config_entry.entry_id] = coordinator

    # reg = dr.async_get(hass)
    # device_entry = reg.async_get_or_create(
    #     config_entry_id=config_entry.entry_id,
    #     identifiers={(DOMAIN, config_entry.unique_id or config_entry.entry_id, 'main')},
    #     manufacturer=coordinator.manufacturer,
    #     name=f"{coordinator.manufacturer} {coordinator.model} {coordinator.serial_number}",
    # )
    # text_heatpump = "Heatpump"
    # reg.async_update_device(
    #     device_id=device_entry.id,
    #     configuration_url=f"http://{host}/",
    #     manufacturer=coordinator.manufacturer,
    #     model=coordinator.model,
    #     name=f"{text_heatpump} {coordinator.serial_number}",
    #     suggested_area="Utility room",
    #     sw_version=coordinator.firmware_version,
    # )

    # if coordinator.has_heating:
    #     text_heating = "Heating"
    #     device_entry_heating = reg.async_get_or_create(
    #         config_entry_id=config_entry.entry_id,
    #         identifiers={(DOMAIN, config_entry.unique_id or config_entry.entry_id, 'heating')},
    #         manufacturer=coordinator.manufacturer,
    #         name=f"{text_heating} {coordinator.serial_number}",
    #     )
    #     reg.async_update_device(
    #         device_id=device_entry_heating.id,
    #         configuration_url=f"http://{host}/",
    #         manufacturer=coordinator.manufacturer,
    #         model=coordinator.model,
    #         name=f"{text_heating} {coordinator.serial_number}",
    #         suggested_area="Utility room",
    #         sw_version=coordinator.firmware_version,
    #     )

    # if coordinator.has_domestic_water:
    #     text_domestic_water = "Domestic water"
    #     device_entry_domestic_water = reg.async_get_or_create(
    #         config_entry_id=config_entry.entry_id,
    #         identifiers={(DOMAIN, config_entry.unique_id or config_entry.entry_id, 'domestic_water')},
    #         manufacturer=coordinator.manufacturer,
    #         name=f"{text_domestic_water} {coordinator.serial_number}",
    #     )
    #     reg.async_update_device(
    #         device_id=device_entry_domestic_water.id,
    #         configuration_url=f"http://{host}/",
    #         manufacturer=coordinator.manufacturer,
    #         model=coordinator.model,
    #         name=f"{text_domestic_water} {coordinator.serial_number}",
    #         suggested_area="Utility room",
    #         sw_version=coordinator.firmware_version,
    #     )

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
