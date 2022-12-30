"""Support for Luxtronik switches."""
# region Imports
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from luxtronik import Calculations, Parameters, Visibilities

from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LuxtronikEntityDescription
from .base import LuxtronikEntity
from .const import (
    CONF_HA_SENSOR_PREFIX,
    DEVICE_KEY_DOMESTIC_WATER,
    DEVICE_KEY_HEATING,
    DEVICE_KEY_HEATPUMP,
    DOMAIN,
    LUX_PARAMETER_MODE_DOMESTIC_WATER,
    LUX_PARAMETER_MODE_HEATING,
    LUX_PARAMETER_REMOTE_MAINTENANCE,
    LuxMode,
)
from .coordinator import LuxtronikCoordinator

# endregion Imports


@dataclass
class LuxtronikSwitchDescription(
    SwitchEntityDescription,
    LuxtronikEntityDescription,
):
    """Class describing Luxtronik switch entities."""

    on_state: str | bool = True
    off_state: str | bool = False
    icon_off: str | None = None
    inverted = False


# All descriptions can be found here. Mostly the Boolean data types in the
# default instruction set of each category end up being a Switch.
SWITCHES: tuple[LuxtronikSwitchDescription, ...] = (
    # Switch
    # ...
    # Main heatpump
    LuxtronikSwitchDescription(
        luxtronik_key=LUX_PARAMETER_REMOTE_MAINTENANCE,
        key="remote_maintenance",
        icon="mdi:remote-desktop",
        entity_category=EntityCategory.CONFIG,
    ),
    LuxtronikSwitchDescription(
        luxtronik_key=LUX_PARAMETER_REMOTE_MAINTENANCE,
        key="remote_maintenance_test",
        icon="mdi:remote-desktop",
        entity_category=EntityCategory.CONFIG,
    ),
)
SWITCHES_HEATING: tuple[LuxtronikSwitchDescription, ...] = (
    # Heating
    LuxtronikSwitchDescription(
        luxtronik_key=LUX_PARAMETER_MODE_HEATING,
        key="heating",
        icon="mdi:radiator",
        icon_off="mdi:radiator-off",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        on_state=LuxMode.automatic.value,
        off_state=LuxMode.off.value,
    ),
)
SWITCHES_DOMESTIC_WATER: tuple[LuxtronikSwitchDescription, ...] = (
    # Domestic water
    LuxtronikSwitchDescription(
        luxtronik_key=LUX_PARAMETER_MODE_DOMESTIC_WATER,
        key="domestic_water",
        icon="mdi:water-boiler-auto",
        icon_off="mdi:water-boiler-off",
        entity_category=EntityCategory.CONFIG,
        device_class=None,
        on_state=LuxMode.automatic.value,
        off_state=LuxMode.off.value,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up luxtronik sensors dynamically through luxtronik discovery."""
    coordinator: LuxtronikCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        LuxtronikSwitchEntity(entry, coordinator, description, DEVICE_KEY_HEATPUMP)
        for description in SWITCHES
    )
    if coordinator.has_heating:
        async_add_entities(
            LuxtronikSwitchEntity(entry, coordinator, description, DEVICE_KEY_HEATING)
            for description in SWITCHES_HEATING
        )
    if coordinator.has_domestic_water:
        async_add_entities(
            LuxtronikSwitchEntity(
                entry, coordinator, description, DEVICE_KEY_DOMESTIC_WATER
            )
            for description in SWITCHES_DOMESTIC_WATER
        )


def _get_sensor_data(
    sensors: dict[str, Parameters | Calculations | Visibilities],
    luxtronik_key: str,
) -> Any:
    """Get sensor data."""
    key = luxtronik_key.split(".")
    return _get_key_value(sensors, key[0], key[1])
    # if key[0] == "parameters":
    #     return sensors.get("parameters").get(key[1]).value
    # elif key[0] == "calculatons":
    #     return sensors.get("calculatons").get(key[1]).value
    # elif key[0] == "visibilities":
    #     return sensors.get("visibilities").get(key[1]).value
    # return None


def _get_key_value(
    sensors: dict[str, Parameters | Calculations | Visibilities],
    main_key: str,
    sub_key: str,
) -> Any:
    main = sensors.get(main_key)
    if main is None:
        return None
    sub = main.get(sub_key)
    if sub is None:
        return None
    return sub.value


class LuxtronikSwitchEntity(LuxtronikEntity, SwitchEntity):
    """Luxtronik Switch Entity."""

    entity_description: LuxtronikSwitchDescription
    _coordinator: LuxtronikCoordinator

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: LuxtronikCoordinator,
        description: LuxtronikSwitchDescription,
        device_info_ident: str,
    ) -> None:
        """Init LuxtronikSwitch."""
        super().__init__(
            coordinator=coordinator,
            description=description,
            device_info_ident=device_info_ident,
        )
        prefix = entry.data[CONF_HA_SENSOR_PREFIX]
        self.entity_id = ENTITY_ID_FORMAT.format(f"{prefix}_{description.key}")
        self._attr_unique_id = self.entity_id
        # self._attr_is_on = False
        self._sensor_data = _get_sensor_data(
            coordinator.data, description.luxtronik_key
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # self._sensor_data
        value = _get_sensor_data(
            self.coordinator.data, self.entity_description.luxtronik_key
        )
        self._attr_is_on = not value if self.entity_description.inverted else value
        super()._handle_coordinator_update()
        # self.async_write_ha_state()

    # @property
    # def is_on(self) -> bool | None:
    #     """Return true if binary sensor is on."""
    #     value = self._sensor_data == self.entity_description.on_state
    #     return not value if self.entity_description.inverted else value

    @property
    def icon(self) -> str | None:
        """Return the icon to be used for this entity."""
        if not self.is_on and self.entity_description.icon_off is not None:
            return self.entity_description.icon_off
        return self.entity_description.icon

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self.coordinator.write(
            self.entity_description.luxtronik_key.split(".")[1],
            self.entity_description.on_state,
            use_debounce=False,
            update_immediately_after_write=True,
        )
        # Update the data
        # self.schedule_update_ha_state(force_refresh=True)
        # await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self.coordinator.write(
            self.entity_description.luxtronik_key.split(".")[1],
            self.entity_description.off_state,
            use_debounce=False,
            update_immediately_after_write=True,
        )
        # Update the data
        # self.schedule_update_ha_state(force_refresh=True)
        # await self.coordinator.async_request_refresh()

    # def update(self) -> None:
    #     """Get the latest status and use it to update our sensor state."""
    #     self.coordinator.update()
