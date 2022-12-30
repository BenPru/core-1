"""Update coordinator for Luxtronik integration."""
# region Imports
from __future__ import annotations

from collections.abc import Awaitable, Callable, Coroutine, Mapping
from datetime import timedelta
from functools import wraps
import json
import os.path
import re
import threading
from typing import Any, Final, TypeVar, Union

import async_timeout
from luxtronik import Calculations, Luxtronik, Parameters, Visibilities
from typing_extensions import Concatenate, ParamSpec

from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import Throttle

from .const import (
    CONF_CALCULATIONS,
    CONF_PARAMETERS,
    CONF_VISIBILITIES,
    DEVICE_KEY_COOLING,
    DEVICE_KEY_DOMESTIC_WATER,
    DEVICE_KEY_HEATING,
    DEVICE_KEY_HEATPUMP,
    DOMAIN,
    LANG_DEFAULT,
    LOGGER,
    LUX_PARAMETER_MK_SENSORS,
    LUX_PARAMETER_SOLAR_DETECT,
    MIN_TIME_BETWEEN_UPDATES,
    PLATFORMS,
    LUX_MODELS_AlphaInnotec,
    LUX_MODELS_Novelan,
    LuxMkTypes,
)

# endregion Imports

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


class LuxtronikCoordinator(
    DataUpdateCoordinator[dict[str, Union[Parameters, Calculations, Visibilities]]]
):
    """Representation of a Luxtronik Coordinator."""

    device_infos = dict[str, DeviceInfo]()
    __ignore_update = False
    __content_locale__ = dict[str, str]()
    __content_sensors_locale__ = dict[str, str]()

    def __init__(
        self,
        hass: HomeAssistant,
        client: Luxtronik,
        config: Mapping[str, Any],
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
            # request_refresh_debouncer=Debouncer(
            #     hass, LOGGER, cooldown=1.0, immediate=False
            # ),
        )
        self._load_translations(hass)
        self._create_device_infos(config)

    async def _async_update_data(
        self,
    ) -> dict[str, Parameters | Calculations | Visibilities]:
        """Connect and fetch data."""
        try:
            if not self.__ignore_update:
                # self.update_interval = 10
                async with async_timeout.timeout(10):
                    self.client.read()
                LOGGER.info("Luxtronik read 860: %s", self.client.parameters.get(860))
                # self.update_interval
                # Set update_interval if needed
        except Exception as err:
            raise UpdateFailed("Error communicating with device") from err
        return {
            "parameters": self.client.parameters,
            "calculations": self.client.calculations,
            "visibilities": self.client.visibilities,
        }

    def _load_translations(self, hass: HomeAssistant):
        """Load translations from file for device and entity names."""
        lang = self._normalize_lang(hass.config.language)
        self.__content_locale__ = self._load_lang_from_file(
            f"translations/texts.{lang}.json"
        )
        for platform in PLATFORMS:
            fname = f"translations/{platform}.{LANG_DEFAULT}.json"
            if self._exists_locale_file(self._build_filepath(fname)):
                self.__content_sensors_locale__[platform] = self._load_lang_from_file(
                    fname
                )

    def _normalize_lang(self, lang: str) -> str:
        if lang is None:
            return LANG_DEFAULT
        lang = lang.lower()
        if "-" in lang:
            lang = lang.split("-")[0]
        fname = self._build_filepath(f"translations/texts.{lang}.json")
        if not self._exists_locale_file(fname):
            return LANG_DEFAULT
        return lang

    def _build_filepath(self, fname: str) -> str:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(dir_path, fname)

    def _exists_locale_file(self, fname: str) -> bool:
        return os.path.isfile(fname)

    def _load_lang_from_file(self, fname: str, log_warning=True):
        fname = self._build_filepath(fname)
        if not self._exists_locale_file(fname):
            if log_warning:
                LOGGER.warning("_load_lang_from_file - file not found %s", fname)
            return {}
        with open(fname, encoding="utf8") as locale_file:
            data = json.loads(locale_file.read())
            return data

    def _create_device_infos(self, config: Mapping[str, Any]):
        host = config[CONF_HOST]
        self.device_infos[DEVICE_KEY_HEATPUMP] = self._build_device_info(
            DEVICE_KEY_HEATPUMP, f"http://{host}/"
        )
        self.device_infos[DEVICE_KEY_HEATING] = self._build_device_info(
            DEVICE_KEY_HEATING, f"http://{host}/"
        )
        self.device_infos[DEVICE_KEY_DOMESTIC_WATER] = self._build_device_info(
            DEVICE_KEY_DOMESTIC_WATER, f"http://{host}/"
        )
        self.device_infos[DEVICE_KEY_COOLING] = self._build_device_info(
            DEVICE_KEY_COOLING, f"http://{host}/"
        )

    def _build_device_info(self, key: str, configuration_url: str) -> DeviceInfo:
        text = self.get_device_entity_title(key)
        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    f"{self.manufacturer}_{self.model}_{self.serial_number}_{key}".lower(),
                )
            },
            configuration_url=configuration_url,
            name=f"{text} S/N {self.serial_number}",
            manufacturer=self.manufacturer,
            model=self.model,
            suggested_area="Utility room",
            sw_version=self.firmware_version,
        )

    def get_device_entity_title(self, key: str) -> str:
        """Get a device or entity title text in locale language."""
        if key in self.__content_locale__:
            return self.__content_locale__[key]
        LOGGER.warning(
            "Get_sensor_text key %s not found in %s", key, self.__content_locale__
        )
        return key.replace("_", " ").title()

    # def get_sensor_value_text(self, key: str, value: str, platform="sensor") -> str:
    #     """Get a sensor value text."""
    #     content = self.__content_sensors_locale__[platform]
    #     # if (
    #     #     "state" in content
    #     #     # and key in content["state"]
    #     #     and content["state"].__contains__(key)
    #     #     # and value in content["state"][key]
    #     #     and content["state"][key].__contains__(value)
    #     # ):
    #     if content["state"][key][value] is not None:
    #         return content["state"][key][value]
    #     LOGGER.warning(
    #         "Get_sensor_value_text key %s / value %s not found in %s",
    #         key,
    #         value,
    #         content,
    #     )
    #     return key.replace("_", " ").title()

    @property
    def serial_number(self) -> str:
        """Return the serial number."""
        serial_number_date = self.get_value("parameters.ID_WP_SerienNummer_DATUM")
        serial_number_hex = hex(
            int(self.get_value("parameters.ID_WP_SerienNummer_HEX"))
        )
        return f"{serial_number_date}-{serial_number_hex}".replace("x", "")

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
        LOGGER.info("Luxtronik read: %s", self.client.parameters.get(860))

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

    # async
    def __write(self, parameter, value, update_immediately_after_write):
        try:
            # with self.lock.acquire(  # pylint: disable=consider-using-with
            #     blocking=True, timeout=self._lock_timeout_sec
            # ) as lock_result:
            #     if lock_result:
            LOGGER.info(
                'LuxtronikDevice.write %s value: "%s" - update_immediately_after_write: %s',
                parameter,
                value,
                update_immediately_after_write,
            )
            self.client.parameters.set(parameter, value)
            self.client.write()
            # event_data = {
            #     "parameter": parameter,
            #     "value": value,
            # }
            # self.hass.bus.async_fire(f"{DOMAIN}_data_update", event_data)

            # else:
            #     LOGGER.warning(
            #         "Couldn't write luxtronik parameter %s with value %s because of lock timeout %s",
            #         parameter,
            #         value,
            #         self._lock_timeout_sec,
            #     )
        finally:
            # self.lock.release()
            # if update_immediately_after_write:
            #     # time.sleep(3)
            #     # await asyncio.sleep(3)
            #     # await self._async_update_data()
            #     # self._async_update_data()
            #     # if not self.__ignore_update:
            #     self.client.read()
            #     self.update_interval = 1
            # # self.__ignore_update = False
            LOGGER.info(
                'LuxtronikDevice.write finished %s value: "%s" - update_immediately_after_write: %s',
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
