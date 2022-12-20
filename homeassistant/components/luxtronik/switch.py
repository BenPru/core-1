"""Support for Luxtronik switches."""
# region Imports
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LuxtronikEntityDescription
from .base import LuxtronikEntity
from .const import (
    CONF_HA_SENSOR_PREFIX,
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
        name="Remote maintenance",
        icon="mdi:remote-desktop",
        entity_category=EntityCategory.CONFIG,
        # device_class=BinarySensorDeviceClass.HEAT,
    ),
)
SWITCHES_HEATING: tuple[LuxtronikSwitchDescription, ...] = (
    # Heating
    LuxtronikSwitchDescription(
        luxtronik_key=LUX_PARAMETER_MODE_HEATING,
        key="heating",
        name="Heating",
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
        name="Domestic water",
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

    # reg = dr.async_get(hass)
    # device = reg.async_get(config_entry_id=entry.entry_id)
    async_add_entities(
        LuxtronikSwitchEntity(entry, coordinator, description, "main")
        for description in SWITCHES
    )
    if coordinator.has_heating:
        async_add_entities(
            LuxtronikSwitchEntity(entry, coordinator, description, "heating")
            for description in SWITCHES_HEATING
        )
    if coordinator.has_domestic_water:
        async_add_entities(
            LuxtronikSwitchEntity(entry, coordinator, description, "domestic_water")
            for description in SWITCHES_DOMESTIC_WATER
        )


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
        super().__init__(luxtronik_key=description.luxtronik_key)
        self._coordinator = coordinator
        self.entity_description = description
        # self._attr_unique_id = f"{super().unique_id}{description.key}"
        prefix = entry.data[CONF_HA_SENSOR_PREFIX]
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN + "_" + device_info_ident, entry.unique_id or entry.entry_id)
            }
        )

        self.entity_id = ENTITY_ID_FORMAT.format(f"{prefix}_{description.key}")
        self._attr_unique_id = self.entity_id

    # @property
    # def device_info(self) -> DeviceInfo:
    #     """Return device information for the main device."""
    #     return DeviceInfo(identifiers={(DOMAIN, self.unique_id)})

    @property
    def is_on(self):
        """Return true if binary sensor is on."""
        value = (
            self._coordinator.get_value(self.entity_description.luxtronik_key)
            == self.entity_description.on_state
        )
        return not value if self.entity_description.inverted else value

    @property
    def icon(self):  # -> str | None:
        """Return the icon to be used for this entity."""
        if not self.is_on and self.entity_description.icon_off is not None:
            return self.entity_description.icon_off
        return self.entity_description.icon

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self._coordinator.write(
            self.entity_description.luxtronik_key.split(".")[1],
            self.entity_description.on_state,
            use_debounce=False,
            update_immediately_after_write=True,
        )
        self.schedule_update_ha_state(force_refresh=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self._coordinator.write(
            self.entity_description.luxtronik_key.split(".")[1],
            self.entity_description.off_state,
            use_debounce=False,
            update_immediately_after_write=True,
        )
        self.schedule_update_ha_state(force_refresh=True)

    def update(self):
        """Get the latest status and use it to update our sensor state."""
        self._coordinator.update()
