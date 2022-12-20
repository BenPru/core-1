"""Luxtronik Home Assistant Base Device Model."""
from __future__ import annotations

from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import LUXTRONIK_HA_SIGNAL_UPDATE_ENTITY


class LuxtronikEntity(Entity):
    """Luxtronik base device."""

    luxtronik_key: str | None = None
    _attr_has_entity_name = True

    def __init__(self, luxtronik_key: str) -> None:
        """Init LuxtronikEntity."""
        # self._attr_unique_id = f"tuya.{device.id}"
        # self.device = device
        # self.device_manager = device_manager
        self.luxtronik_key = luxtronik_key

    @property
    def device_info(self) -> DeviceInfo:
        """Return a device description for device registry."""
        return DeviceInfo(
            # identifiers={(DOMAIN, self.device.id)},
            manufacturer="Luxtronik",
            # name=self.device.name,
            # model=f"{self.device.product_name} ({self.device.product_id})",
        )

    async def async_added_to_hass(self) -> None:
        """Call when entity is added to hass."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LUXTRONIK_HA_SIGNAL_UPDATE_ENTITY}",
                # f"{LUXTRONIK_HA_SIGNAL_UPDATE_ENTITY}_{self.device.id}",
                self.async_write_ha_state,
            )
        )
