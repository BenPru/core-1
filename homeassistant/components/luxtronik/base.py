"""Luxtronik Home Assistant Base Device Model."""
from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import LuxtronikEntityDescription
from .coordinator import LuxtronikCoordinator


class LuxtronikEntity(CoordinatorEntity[LuxtronikCoordinator]):
    """Luxtronik base device."""

    luxtronik_key: str | None = None
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LuxtronikCoordinator,
        description: LuxtronikEntityDescription,
        device_info_ident: str,
    ) -> None:
        """Init LuxtronikEntity."""
        super().__init__(coordinator=coordinator)
        self.entity_description = description
        # self.coordinator = coordinator
        self._attr_device_info = coordinator.device_infos[device_info_ident]
        # self._attr_unique_id = f"tuya.{device.id}"
        self.luxtronik_key = description.luxtronik_key

        self._attr_name = coordinator.get_device_entity_title(description.key)

    # @property
    # def available(self) -> bool:
    #     """Return if entity is available."""
    #     return True

    # @callback
    # async def _handle_coordinator_update(self) -> None:
    #     """Handle updated data from the coordinator."""
    #     value = (
    #         self.coordinator.get_value(self.entity_description.luxtronik_key)
    #         == self.entity_description.on_state
    #     )
    #     self._attr_is_on = not value if self.entity_description.inverted else value
    #     # self.async_write_ha_state()
    #     await super()._handle_coordinator_update()

    # async def async_added_to_hass(self) -> None:
    #     """Call when entity is added to hass."""
    #     self.async_on_remove(
    #         async_dispatcher_connect(
    #             self.hass,
    #             f"{LUXTRONIK_HA_SIGNAL_UPDATE_ENTITY}",
    #             # f"{LUXTRONIK_HA_SIGNAL_UPDATE_ENTITY}_{self.device.id}",
    #             self.async_write_ha_state,
    #         )
    #     )
