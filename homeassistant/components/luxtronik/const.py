"""Constants for Luxtronik heatpump integration."""
# region Imports
from datetime import timedelta
from enum import Enum
import logging
from typing import Final

# endregion Imports

# region Constants Main
DOMAIN: Final = "luxtronik"
NICKNAME_PREFIX: Final = "Home Assistant"

LOGGER: Final[logging.Logger] = logging.getLogger(__package__)
PLATFORMS: list[str] = ["switch"]  # "sensor", "binary_sensor", "climate", "number",

DEVICE_KEY_HEATPUMP: Final = "heatpump"
DEVICE_KEY_HEATING: Final = "heating"
DEVICE_KEY_DOMESTIC_WATER: Final = "domestic_water"
DEVICE_KEY_COOLING: Final = "cooling"

LUXTRONIK_HA_SIGNAL_UPDATE_ENTITY = "luxtronik_entry_update"

MIN_TIME_BETWEEN_UPDATES: Final = timedelta(seconds=10)
# endregion Constants Main

# region Conf

CONF_PARAMETERS: Final = "parameters"
CONF_CALCULATIONS: Final = "calculations"
CONF_VISIBILITIES: Final = "visibilities"

CONF_HA_SENSOR_PREFIX: Final = "ha_sensor_prefix"
CONF_UPDATE_IMMEDIATELY_AFTER_WRITE: Final = "update_immediately_after_write"
CONF_CONTROL_MODE_HOME_ASSISTANT: Final = "control_mode_home_assistant"
CONF_HA_SENSOR_INDOOR_TEMPERATURE: Final = "ha_sensor_indoor_temperature"

CONF_LOCK_TIMEOUT: Final = "lock_timeout"
CONF_SAFE: Final = "safe"

DEFAULT_PORT: Final = 8889

LANG_EN: Final = "en"
LANG_DE: Final = "de"
LANG_DEFAULT: Final = LANG_EN
LANGUAGES: Final = Enum("en", "de")
LANGUAGES_SENSOR_NAMES: Final = [LANG_EN, LANG_DE]


class LuxMode(Enum):
    """Luxmodes off etc."""

    off: Final = "Off"
    automatic: Final = "Automatic"
    second_heatsource: Final = "Second heatsource"
    party: Final = "Party"
    holidays: Final = "Holidays"


class LuxMkTypes(Enum):
    """LuxMkTypes etc."""

    off: Final = 0
    discharge: Final = 1
    load: Final = 2
    cooling: Final = 3
    heating_cooling: Final = 4


# endregion Conf

LUX_PARAMETER_MK_SENSORS: Final = [
    "parameters.ID_Einst_MK1Typ_akt",
    "parameters.ID_Einst_MK2Typ_akt",
    "parameters.ID_Einst_MK3Typ_akt",
]
LUX_PARAMETER_SOLAR_DETECT: Final = "parameters.ID_BSTD_Solar"
LUX_PARAMETER_SERIAL_NUMBER: Final = "parameters.ID_WP_SerienNummer_DATUM"
LUX_PARAMETER_MODE_HEATING: Final = "parameters.ID_Ba_Hz_akt"
LUX_PARAMETER_MODE_DOMESTIC_WATER: Final = "parameters.ID_Ba_Bw_akt"
LUX_PARAMETER_REMOTE_MAINTENANCE: Final = "parameters.ID_Einst_Fernwartung_akt"

LUX_MODELS_AlphaInnotec = ["LWP", "LWV", "MSW", "SWC", "SWP"]
LUX_MODELS_Novelan = ["BW", "LA", "LD", "LI", "SI", "ZLW"]
LUX_MODELS_Other = ["CB", "CI", "CN", "CS"]
