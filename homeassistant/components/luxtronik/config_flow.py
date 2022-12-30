"""Config flow to configure the Luxtronik heatpump controller integration."""
# region Imports
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from luxtronik import Luxtronik
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.dhcp import DhcpServiceInfo
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_CONTROL_MODE_HOME_ASSISTANT,
    CONF_HA_SENSOR_INDOOR_TEMPERATURE,
    CONF_HA_SENSOR_PREFIX,
    DEFAULT_PORT,
    DOMAIN,
    LOGGER,
)
from .coordinator import LuxtronikCoordinator
from .lux_helper import discover

# endregion Imports

PORT_SELECTOR = vol.All(
    selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1, step=1, max=65535, mode=selector.NumberSelectorMode.BOX
        )
    ),
    vol.Coerce(int),
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="wp-novelan"): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): PORT_SELECTOR,
    }
)


def _get_options_schema(options) -> vol.Schema:
    """Build and return the options schema."""
    return vol.Schema(
        {
            vol.Optional(
                CONF_HA_SENSOR_INDOOR_TEMPERATURE,
                default=f"sensor.{DOMAIN}_room_temperature",
                description={
                    "suggested_value": None
                    if options is None
                    else options.get(CONF_HA_SENSOR_INDOOR_TEMPERATURE)
                },
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=Platform.SENSOR)
            ),
            # vol.Optional(CONF_CONTROL_MODE_HOME_ASSISTANT, default=False): bool,
            vol.Required(
                CONF_HA_SENSOR_PREFIX,
                default="luxtronik",
                description={
                    "suggested_value": None
                    if options is None
                    else options.get(CONF_HA_SENSOR_PREFIX)
                },
            ): str,
        }
    )


# CONFIG_SCHEMA = STEP_OPTIONS_DATA_SCHEMA


class LuxtronikFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Luxtronik heatpump controller config flow."""

    VERSION = 1
    _hassio_discovery = None
    _discovery_host = None
    _discovery_port = None
    _discovery_schema = None

    _sensor_prefix = DOMAIN
    _title = "Luxtronik"

    def _get_schema(self):
        return vol.Schema(
            {
                vol.Required(CONF_HOST, default=self._discovery_host): str,
                vol.Required(CONF_PORT, default=self._discovery_port): int,
                vol.Optional(CONF_CONTROL_MODE_HOME_ASSISTANT, default=False): bool,
                vol.Optional(
                    CONF_HA_SENSOR_INDOOR_TEMPERATURE,
                    default=f"sensor.{self._sensor_prefix}_room_temperature",
                ): str,
            }
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )
        return await self.async_step_options(user_input)

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""
        return self._title

    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow option step."""

        if "data" not in self.context:
            self.context["data"] = {}
        self.context["data"] |= user_input
        data = self.context["data"]

        try:
            client = Luxtronik(host=data[CONF_HOST], port=data[CONF_PORT], safe=False)
        except Exception:  # pylint: disable=broad-except
            return self.async_abort(reason="cannot_connect")
        coordinator = LuxtronikCoordinator(
            hass=self.hass,
            client=client,
            config=data,
        )
        self._title = (
            title
        ) = f"{coordinator.manufacturer} {coordinator.model} {coordinator.serial_number}"
        name = f"{title} ({data[CONF_HOST]}:{data[CONF_PORT]})"

        unique_id = f"{coordinator.manufacturer}_{coordinator.model}_{coordinator.serial_number}".lower()
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        if user_input is not None and CONF_HA_SENSOR_INDOOR_TEMPERATURE in user_input:
            return self.async_create_entry(title=title, data=data)
        return self.async_show_form(
            step_id="options",
            data_schema=_get_options_schema(None),
            description_placeholders={"name": name},
        )

    async def async_step_dhcp(self, discovery_info: DhcpServiceInfo) -> FlowResult:
        """Prepare configuration for a DHCP discovered Luxtronik heatpump."""
        LOGGER.info(
            "Found device with hostname '%s' IP '%s'",
            discovery_info.hostname,
            discovery_info.ip,
        )
        # Validate dhcp result with socket broadcast:
        broadcast_discover_ip, broadcast_discover_port = discover()
        if broadcast_discover_ip != discovery_info.ip:
            return self.async_abort(reason="no_devices_found")
        client = Luxtronik(
            host=broadcast_discover_ip, port=broadcast_discover_ip, safe=False
        )
        config = dict[str, Any]()
        config[CONF_HOST] = broadcast_discover_ip
        coordinator = LuxtronikCoordinator(
            hass=self.hass,
            client=client,
            config=config,
        )
        unique_id = f"{coordinator.manufacturer} {coordinator.model} {coordinator.serial_number}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        self._discovery_host = discovery_info.ip
        self._discovery_port = (
            DEFAULT_PORT if broadcast_discover_port is None else broadcast_discover_port
        )
        self._discovery_schema = self._get_schema()
        return await self.async_step_user()

    async def _show_setup_form(
        self, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
            data_schema=self._get_schema(),
            errors=errors or {},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get default options flow."""
        return LuxtronikOptionsFlowHandler(config_entry)


class LuxtronikOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a Luxtronik options flow."""

    _sensor_prefix = DOMAIN

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    def _get_value(self, key: str, default=None):
        """Return a value from Luxtronik."""
        return self.config_entry.options.get(
            key, self.config_entry.data.get(key, default)
        )

    def _get_options_schema(self):
        """Return a schema for Luxtronik configuration options."""
        return vol.Schema(
            {
                vol.Optional(
                    CONF_CONTROL_MODE_HOME_ASSISTANT,
                    default=self._get_value(CONF_CONTROL_MODE_HOME_ASSISTANT, False),
                ): bool,
                vol.Optional(
                    CONF_HA_SENSOR_INDOOR_TEMPERATURE,
                    default=self._get_value(
                        CONF_HA_SENSOR_INDOOR_TEMPERATURE,
                        f"sensor.{self._sensor_prefix}_room_temperature",
                    ),
                ): str,
            }
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        client = Luxtronik(
            host=self.config_entry.data[CONF_HOST],
            port=self.config_entry.data[CONF_PORT],
            safe=False,
        )
        coordinator = LuxtronikCoordinator(
            hass=self.hass,
            client=client,
            config=self.config_entry.data,
        )
        title = f"{coordinator.manufacturer} {coordinator.model} {coordinator.serial_number}"
        name = f"{title} ({self.config_entry.data[CONF_HOST]}:{self.config_entry.data[CONF_PORT]})"
        return self.async_show_form(
            step_id="user",
            data_schema=_get_options_schema(None),
            description_placeholders={"name": name},
        )


# """Config flow to configure the luxtronik heatpump integration."""
# # region Imports
# from typing import Any

# from luxtronik import Luxtronik
# import voluptuous as vol

# from homeassistant import config_entries
# from homeassistant.config_entries import ConfigEntry
# from homeassistant.const import CONF_HOST, CONF_PORT
# from homeassistant.core import callback
# from homeassistant.data_entry_flow import FlowResult
# from homeassistant.helpers import instance_id
# from homeassistant.util.network import is_host_valid

# from .const import DOMAIN, LUX_PARAMETER_SERIAL_NUMBER, NICKNAME_PREFIX

# # endregion Imports


# class LuxtronikOptionsFlowHandler(config_entries.OptionsFlowWithConfigEntry):
#     """Config flow options for Luxtronik."""

#     _discovery_host: str = None
#     _discovery_port: int = None

#     data_schema: vol.Schema

#     async def async_step_init(self, user_input: dict[str, Any] = None) -> FlowResult:
#         """Manage the options."""
#         # coordinator: LuxtronikCoordinator
#         # coordinator = self.hass.data[DOMAIN][self.config_entry.entry_id]

#         host = self._discovery_host
#         if CONF_HOST in user_input:
#             host = user_input[CONF_HOST]
#         port = self._discovery_port
#         if CONF_PORT in user_input:
#             port = user_input[CONF_PORT]

#         self.data_schema = vol.Schema(
#             {
#                 vol.Required(CONF_HOST, default=host): str,
#                 vol.Required(CONF_PORT, default=port): int,
#             }
#         )

#         return await self.async_step_user()

#     async def async_step_user(self, user_input: dict[str, Any] = None) -> FlowResult:
#         """Handle a flow initialized by the user."""
#         if user_input is not None:
#             return self.async_create_entry(title="", data=user_input)

#         return self.async_show_form(
#             step_id="user",
#             data_schema=self.add_suggested_values_to_schema(
#                 self.data_schema, self.options
#             ),
#         )


# class LuxtronikConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
#     """Handle a config flow for Luxtronik integration."""

#     VERSION = 1

#     def __init__(self) -> None:
#         """Initialize config flow."""
#         self.client: Luxtronik = None
#         self.device_config: dict[str, Any] = {}
#         self.entry: ConfigEntry = None
#         self.client_id: str = ""
#         self.nickname: str = ""

#     @staticmethod
#     @callback
#     def async_get_options_flow(
#         config_entry: ConfigEntry,
#     ) -> LuxtronikOptionsFlowHandler:
#         """Luxtronik options callback."""
#         return LuxtronikOptionsFlowHandler(config_entry)

#     def create_client(self) -> None:
#         """Create Luxtronik client from config."""
#         host = self.device_config[CONF_HOST]
#         port = self.device_config[CONF_PORT]
#         self.client = Luxtronik(host=host, port=port, safe=False)

#     async def async_create_device(self) -> FlowResult:
#         """Initialize and create Luxtronik device from config."""
#         assert self.client

#         self.client.read()
#         serial_number = self.client.get_value(LUX_PARAMETER_SERIAL_NUMBER)
#         cid = serial_number.lower()
#         title = self.device_config[CONF_HOST]

#         await self.async_set_unique_id(cid)
#         self._abort_if_unique_id_configured()

#         return self.async_create_entry(title=title, data=self.device_config)

#     async def async_step_user(self, user_input: dict[str, Any] = None) -> FlowResult:
#         """Handle the initial step."""
#         errors: dict[str, str] = {}

#         if user_input is not None:
#             host = user_input[CONF_HOST]
#             if is_host_valid(host):
#                 self.device_config[CONF_HOST] = host
#                 self.create_client()

#         return self.async_show_form(
#             step_id="user",
#             data_schema=vol.Schema({vol.Required(CONF_HOST, default=""): str}),
#             errors=errors,
#         )

#     async def gen_instance_ids(self) -> tuple[str, str]:
#         """Generate client_id and nickname."""
#         uuid = await instance_id.async_get(self.hass)
#         return uuid, f"{NICKNAME_PREFIX} {uuid[:6]}"
