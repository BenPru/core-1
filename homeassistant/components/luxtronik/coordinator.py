"""Update coordinator for Luxtronik integration."""
import asyncio
from collections.abc import Awaitable, Callable, Coroutine
from datetime import timedelta
from functools import wraps
import re
import threading
from typing import Any, Final, TypeVar

from luxtronik import Luxtronik
from typing_extensions import Concatenate, ParamSpec

from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import Throttle

from .const import (
    CONF_CALCULATIONS,
    CONF_PARAMETERS,
    CONF_VISIBILITIES,
    DOMAIN,
    LOGGER,
    LUX_PARAMETER_MK_SENSORS,
    LUX_PARAMETER_SOLAR_DETECT,
    MIN_TIME_BETWEEN_UPDATES,
    LUX_MODELS_AlphaInnotec,
    LUX_MODELS_Novelan,
    LuxMkTypes,
)

_LuxtronikCoordinatorT = TypeVar("_LuxtronikCoordinatorT", bound="LuxtronikCoordinator")
_P = ParamSpec("_P")

SCAN_INTERVAL: Final = timedelta(seconds=10)


def catch_luxtronik_errors(
    func: Callable[Concatenate[_LuxtronikCoordinatorT, _P], Awaitable[None]]
) -> Callable[Concatenate[_LuxtronikCoordinatorT, _P], Coroutine[Any, Any, None]]:
    """Catch Luxtronik errors."""

    @wraps(func)
    async def wrapper(
        self: _LuxtronikCoordinatorT,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> None:
        """Catch Luxtronik errors and log message."""
        try:
            await func(self, *args, **kwargs)
        except Exception as err:  # pylint: disable=broad-except
            LOGGER.error("Command error: %s", err)
        await self.async_request_refresh()

    return wrapper


class LuxtronikCoordinator(DataUpdateCoordinator[None]):
    """Representation of a Luxtronik Coordinator."""

    __ignore_update = False

    def __init__(
        self,
        hass: HomeAssistant,
        client: Luxtronik,
        # config: MappingProxyType[str, Any],
        lock_timeout_sec: int = 30,
    ) -> None:
        """Initialize Luxtronik Client."""

        self.lock = threading.Lock()
        self.client = client
        self.update_immediately_after_write = True
        # self.update_immediately_after_write = (
        #     config[CONF_UPDATE_IMMEDIATELY_AFTER_WRITE]
        #     if CONF_UPDATE_IMMEDIATELY_AFTER_WRITE in config
        #     else True
        # )
        self._lock_timeout_sec = lock_timeout_sec

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            request_refresh_debouncer=Debouncer(
                hass, LOGGER, cooldown=1.0, immediate=False
            ),
        )

        # self.device_info = DeviceInfo(
        #     identifiers={(DOMAIN, entry.unique_id or entry.entry_id, device_info_ident)}
        # )

    # reg = dr.async_get(hass)
    # device_entry = reg.async_get_or_create(
    #     config_entry_id=config_entry.entry_id,
    #     identifiers={(DOMAIN, config_entry.unique_id or config_entry.entry_id, "main")},
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
    #         identifiers={
    #             (DOMAIN, config_entry.unique_id or config_entry.entry_id, "heating")
    #         },
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
    #         identifiers={
    #             (
    #                 DOMAIN,
    #                 config_entry.unique_id or config_entry.entry_id,
    #                 "domestic_water",
    #             )
    #         },
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

    @property
    def serial_number(self) -> str:
        """Return the serial number."""
        return self.get_value("parameters.ID_WP_SerienNummer_DATUM")

    @property
    def model(self) -> str:
        """Return the heatpump model."""
        return self.get_value("calculations.ID_WEB_Code_WP_akt")

    @property
    def manufacturer(self) -> str:
        """Return the heatpump manufacturer."""
        return self.__get_manufacturer_by_model(self.model)

    @property
    def firmware_version(self) -> str:
        """Return the heatpump firmware version."""
        return str(self.get_value("calculations.ID_WEB_SoftStand"))

    @property
    def has_heating(self) -> bool:
        """Is heating activated."""
        return True

    @property
    def has_domestic_water(self) -> bool:
        """Is domestic water activated."""
        return True

    async def _async_update_data(self) -> None:
        """Connect and fetch data."""
        if self.__ignore_update:
            return
        try:
            self.client.read()
            # Set update_interval if needed
            # self.update_interval = 10
        except Exception as err:
            raise UpdateFailed("Error communicating with device") from err

    def get_value(self, group_sensor_id: str):
        """Get a sensor value from Luxtronik."""
        sensor = self.get_sensor_by_id(group_sensor_id)
        if sensor is None:
            return None
        return sensor.value

    def get_sensor_by_id(self, group_sensor_id: str):
        """Get a sensor object by id from Luxtronik."""
        try:
            group = group_sensor_id.split(".")[0]
            sensor_id = group_sensor_id.split(".")[1]
            return self.get_sensor(group, sensor_id)
        except IndexError as error:
            LOGGER.critical(group_sensor_id, error, exc_info=True)

    def get_sensor(self, group, sensor_id):
        """Get sensor by configured sensor ID."""
        sensor = None
        if group == CONF_PARAMETERS:
            sensor = self.client.parameters.get(sensor_id)
        if group == CONF_CALCULATIONS:
            sensor = self.client.calculations.get(sensor_id)
        if group == CONF_VISIBILITIES:
            sensor = self.client.visibilities.get(sensor_id)
        return sensor

    def detect_cooling_mk(self):
        """We iterate over the mk sensors, detect cooling and return a list of parameters that are may show cooling is enabled."""
        cooling_mk = []
        for mk_sensor in LUX_PARAMETER_MK_SENSORS:
            sensor_value = self.get_value(mk_sensor)
            # LOGGER.info(f"{Mk} = {sensor_value}")
            if sensor_value in [
                LuxMkTypes.cooling.value,
                LuxMkTypes.heating_cooling.value,
            ]:
                cooling_mk = cooling_mk + [mk_sensor]

        # LOGGER.info(f"CoolingMk = {cooling_mk}")
        return cooling_mk

    def detect_solar_present(self) -> bool:
        """Detect and returns True if solar is present."""
        sensor_value = bool(self.get_value(LUX_PARAMETER_SOLAR_DETECT))
        solar_present = sensor_value > 0.01
        # LOGGER.info(f"SolarPresent = {solar_present}")
        return solar_present

    def detect_cooling_present(self) -> bool:
        """Detect and returns True if Cooling is present."""
        cooling_present = len(self.detect_cooling_mk()) > 0
        # LOGGER.info(f"CoolingPresent = {cooling_present}")
        return cooling_present

    def detect_cooling_target_temperature_sensor(self):
        """
        If only 1 MK parameter related to cooling is returned.

        The corresponding cooling_target_temperature sensor is returned.
        """
        mk_param = self.detect_cooling_mk()
        if len(mk_param) == 1:
            mk_number = re.findall("[0-9]+", mk_param[0])[0]
            cooling_target_temperature_sensor = (
                f"parameters.ID_Sollwert_KuCft{mk_number}_akt"
            )
        else:
            cooling_target_temperature_sensor = None
        # LOGGER.info(
        #     f"cooling_target_temperature_sensor = '{cooling_target_temperature_sensor}' "
        # )
        return cooling_target_temperature_sensor

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update sensor values."""
        if self.__ignore_update:
            return
        self.client.read()

    def write(
        self, parameter, value, use_debounce=True, update_immediately_after_write=False
    ):
        """Write a parameter to the Luxtronik heatpump."""
        self.__ignore_update = True
        if use_debounce:
            self.__write_debounced(parameter, value, update_immediately_after_write)
        else:
            self.__write(parameter, value, update_immediately_after_write)

    # @debounce(3)
    def __write_debounced(self, parameter, value, update_immediately_after_write):
        self.__write(parameter, value, update_immediately_after_write)

    async def __write(self, parameter, value, update_immediately_after_write):
        try:
            with self.lock.acquire(  # pylint: disable=consider-using-with
                blocking=True, timeout=self._lock_timeout_sec
            ) as lock_result:
                if lock_result:
                    LOGGER.info(
                        'LuxtronikDevice.write %s value: "%s" - %s',
                        parameter,
                        value,
                        update_immediately_after_write,
                    )
                    self.client.parameters.set(parameter, value)
                    self.client.write()
                    event_data = {
                        "parameter": parameter,
                        "value": value,
                    }
                    self.hass.bus.async_fire(f"{DOMAIN}_data_update", event_data)
                else:
                    LOGGER.warning(
                        "Couldn't write luxtronik parameter %s with value %s because of lock timeout %s",
                        parameter,
                        value,
                        self._lock_timeout_sec,
                    )
        finally:
            self.lock.release()
            if update_immediately_after_write:
                # time.sleep(3)
                await asyncio.sleep(3)
                await self._async_update_data()
            self.__ignore_update = False
            LOGGER.info(
                'LuxtronikDevice.write finished %s value: "%s" - %s',
                parameter,
                value,
                update_immediately_after_write,
            )

    def __get_manufacturer_by_model(self, model: str) -> str:
        """Return the manufacturer."""
        if model is None:
            return ""  # None
        if model.startswith(tuple(LUX_MODELS_Novelan)):
            return "Novelan"
        if model.startswith(tuple(LUX_MODELS_AlphaInnotec)):
            return "Alpha Innotec"
        return ""  # None

    async def async_shutdown(self):
        """Make sure a coordinator is shut down as well as it's connection."""
