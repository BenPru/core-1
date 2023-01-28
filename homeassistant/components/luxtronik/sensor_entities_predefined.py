"""Luxtronik sensors definitions."""
# region Imports
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.helpers.entity import EntityCategory

from .const import (
    LUX_STATE_ICON_MAP,
    SECOUND_TO_HOUR_FACTOR,
    DeviceKey,
    LuxCalculation,
    LuxParameter,
    LuxVisibility,
)
from .model import LuxtronikSensorDescription

# endregion Imports

SENSORS: list[LuxtronikSensorDescription] = [
    # region Main heatpump
    LuxtronikSensorDescription(
        key="status",
        luxtronik_key=LuxCalculation.C0080_STATUS,
        icon_by_state=LUX_STATE_ICON_MAP,
        device_class=SensorDeviceClass.ENUM,
        options=[
            "heating",
            "hot water",
            "swimming pool/solar",
            "evu",
            "defrost",
            "heating external source",
            "cooling",
            "no request",
        ],
        # Check extra_attributes
    ),
    LuxtronikSensorDescription(
        key="status_time",
        luxtronik_key=LuxCalculation.C0120_STATUS_TIME,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:timer-sand",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_registry_visible_default=False,
        # Check extra_attributes
    ),
    LuxtronikSensorDescription(
        key="status_line_1",
        luxtronik_key=LuxCalculation.C0117_STATUS_LINE_1,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:numeric-1-circle",
        entity_registry_visible_default=False,
        device_class=SensorDeviceClass.ENUM,
        options=[
            "heatpump running",
            "heatpump idle",
            "heatpump coming",
            "errorcode slot 0",
            "defrost",
            "witing on LIN connection",
            "compressor heating up",
            "pump forerun",
        ],
        # translation_key="status1",
    ),
    LuxtronikSensorDescription(
        key="status_line_2",
        luxtronik_key=LuxCalculation.C0118_STATUS_LINE_2,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:numeric-2-circle",
        entity_registry_visible_default=False,
        device_class=SensorDeviceClass.ENUM,
        options=["since", "in"],
        # translation_key="status2",
    ),
    LuxtronikSensorDescription(
        key="status_line_3",
        luxtronik_key=LuxCalculation.C0119_STATUS_LINE_3,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:numeric-3-circle",
        entity_registry_visible_default=False,
        device_class=SensorDeviceClass.ENUM,
        options=[
            "heating",
            "no request",
            "grid switch on delay",
            "cycle lock",
            "lock time",
            "domestic water",
            "info bake out program",
            "defrost",
            "pump forerun",
            "thermal desinfection",
            "cooling",
            "swimming pool/solar",
            "heating external energy source",
            "domestic water external energy source",
            "flow monitoring",
            "second heat generator 1 active",
        ],
        # translation_key="status3",
    ),
    LuxtronikSensorDescription(
        key="heat_source_input_temperature",
        luxtronik_key=LuxCalculation.C0204_HEAT_SOURCE_INPUT_TEMPERATURE,
        icon="mdi:thermometer",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
    ),
    LuxtronikSensorDescription(
        key="outdoor_temperature",
        luxtronik_key=LuxCalculation.C0015_OUTDOOR_TEMPERATURE,
        icon="mdi:thermometer",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    LuxtronikSensorDescription(
        key="outdoor_temperature_average",
        luxtronik_key=LuxCalculation.C0016_OUTDOOR_TEMPERATURE_AVERAGE,
        icon="mdi:thermometer",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
    ),
    LuxtronikSensorDescription(
        key="compressor1_impulses",
        luxtronik_key=LuxCalculation.C0057_COMPRESSOR1_IMPULSES,
        icon="mdi:pulse",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="\u2211",
        entity_registry_enabled_default=False,
        visibility=LuxVisibility.V0081_COMPRESSOR1_IMPULSES,
    ),
    LuxtronikSensorDescription(
        key="compressor1_operation_hours",
        luxtronik_key=LuxCalculation.C0056_COMPRESSOR1_OPERATION_HOURS,
        icon="mdi:timer-sand",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.HOURS,
        visibility=LuxVisibility.V0080_COMPRESSOR1_OPERATION_HOURS,
        factor=SECOUND_TO_HOUR_FACTOR,
        decimal_places=0,
    ),
    LuxtronikSensorDescription(
        key="compressor2_impulses",
        luxtronik_key=LuxCalculation.C0059_COMPRESSOR2_IMPULSES,
        icon="mdi:pulse",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="\u2211",
        entity_registry_enabled_default=False,
        visibility=LuxVisibility.V0084_COMPRESSOR2_IMPULSES,
    ),
    LuxtronikSensorDescription(
        key="compressor2_operation_hours",
        luxtronik_key=LuxCalculation.C0058_COMPRESSOR2_OPERATION_HOURS,
        icon="mdi:timer-sand",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.HOURS,
        visibility=LuxVisibility.V0083_COMPRESSOR2_OPERATION_HOURS,
        factor=SECOUND_TO_HOUR_FACTOR,
        decimal_places=0,
    ),
    LuxtronikSensorDescription(
        key="operation_hours",
        luxtronik_key=LuxCalculation.C0063_OPERATION_HOURS,
        icon="mdi:timer-sand",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.HOURS,
        factor=SECOUND_TO_HOUR_FACTOR,
        decimal_places=0,
    ),
    LuxtronikSensorDescription(
        key="heat_amount_counter",
        luxtronik_key=LuxCalculation.C0154_HEAT_AMOUNT_COUNTER,
        icon="mdi:lightning-bolt-circle",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        decimal_places=1,
    ),
    LuxtronikSensorDescription(
        key="hot_gas_temperature",
        luxtronik_key=LuxCalculation.C0014_HOT_GAS_TEMPERATURE,
        icon="mdi:thermometer",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        visibility=LuxVisibility.V0027_HOT_GAS_TEMPERATURE,
    ),
    LuxtronikSensorDescription(
        key="suction_compressor_temperature",
        luxtronik_key=LuxCalculation.C0176_SUCTION_COMPRESSOR_TEMPERATURE,
        icon="mdi:thermometer",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        visibility=LuxVisibility.V0289_SUCTION_COMPRESSOR_TEMPERATURE,
    ),
    LuxtronikSensorDescription(
        key="suction_evaporator_temperature",
        luxtronik_key=LuxCalculation.C0175_SUCTION_EVAPORATOR_TEMPERATURE,
        icon="mdi:thermometer",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        visibility=LuxVisibility.V0310_SUCTION_EVAPORATOR_TEMPERATURE,
    ),
    LuxtronikSensorDescription(
        key="compressor_heating_temperature",
        luxtronik_key=LuxCalculation.C0177_COMPRESSOR_HEATING_TEMPERATURE,
        icon="mdi:thermometer",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        visibility=LuxVisibility.V0290_COMPRESSOR_HEATING_TEMPERATURE,
    ),
    LuxtronikSensorDescription(
        key="overheating_temperature",
        luxtronik_key=LuxCalculation.C0178_OVERHEATING_TEMPERATURE,
        icon="mdi:thermometer",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.KELVIN,
        visibility=LuxVisibility.V0291_OVERHEATING_TEMPERATURE,
    ),
    LuxtronikSensorDescription(
        key="overheating_target_temperature",
        luxtronik_key=LuxCalculation.C0179_OVERHEATING_TARGET_TEMPERATURE,
        icon="mdi:thermometer",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.KELVIN,
        visibility=LuxVisibility.V0291_OVERHEATING_TEMPERATURE,
    ),
    LuxtronikSensorDescription(
        key="high_pressure",
        luxtronik_key=LuxCalculation.C0180_HIGH_PRESSURE,
        icon="mdi:gauge-full",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.BAR,
        visibility=LuxVisibility.V0292_LIN_PRESSURE,
    ),
    LuxtronikSensorDescription(
        key="low_pressure",
        luxtronik_key=LuxCalculation.C0181_LOW_PRESSURE,
        icon="mdi:gauge-low",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.BAR,
        visibility=LuxVisibility.V0292_LIN_PRESSURE,
    ),
    LuxtronikSensorDescription(
        key="additional_heat_generator_operation_hours",
        luxtronik_key=LuxCalculation.C0060_ADDITIONAL_HEAT_GENERATOR_OPERATION_HOURS,
        icon="mdi:timer-sand",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfTime.HOURS,
        visibility=LuxVisibility.V0086_ADDITIONAL_HEAT_GENERATOR_OPERATION_HOURS,
        factor=SECOUND_TO_HOUR_FACTOR,
        decimal_places=0,
    ),
    LuxtronikSensorDescription(
        key="additional_heat_generator_amount_counter",
        luxtronik_key=LuxParameter.P1059_ADDITIONAL_HEAT_GENERATOR_AMOUNT_COUNTER,
        icon="mdi:lightning-bolt-circle",
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        invisible_if_value=0.0,
        visibility=LuxVisibility.V0324_ADDITIONAL_HEAT_GENERATOR_AMOUNT_COUNTER,
        factor=0.1,
        decimal_places=1,
    ),
    LuxtronikSensorDescription(
        key="analog_out1",
        luxtronik_key=LuxCalculation.C0156_ANALOG_OUT1,
        icon="mdi:alpha-v-circle-outline",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        visibility=LuxVisibility.V0248_ANALOG_OUT1,
        entity_registry_enabled_default=False,
        factor=0.1,
    ),
    LuxtronikSensorDescription(
        key="analog_out2",
        luxtronik_key=LuxCalculation.C0157_ANALOG_OUT2,
        icon="mdi:alpha-v-circle-outline",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        visibility=LuxVisibility.V0249_ANALOG_OUT2,
        entity_registry_enabled_default=False,
        factor=0.1,
    ),
    LuxtronikSensorDescription(
        key="current_heat_output",
        luxtronik_key=LuxCalculation.C0257_CURRENT_HEAT_OUTPUT,
        icon="mdi:lightning-bolt-circle",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.ENERGY,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_registry_enabled_default=False,
        decimal_places=0,
    ),
    LuxtronikSensorDescription(
        key="pump_frequency",
        luxtronik_key=LuxCalculation.C0231_PUMP_FREQUENCY,
        icon="mdi:sine-wave",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        entity_registry_enabled_default=False,
    ),
    LuxtronikSensorDescription(
        key="heat_source_output_temperature",
        luxtronik_key=LuxCalculation.C0020_HEAT_SOURCE_OUTPUT_TEMPERATURE,
        icon="mdi:thermometer",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
        invisible_if_value=-50.0,
        visibility=LuxVisibility.V0291_OVERHEATING_TEMPERATURE,
    ),
    # Check
    # LuxtronikIndexStatusSensor(
    #     key_index=None,
    #     key_timestamp_template=None,
    #     luxtronik=luxtronik,
    #     device_info=device_info,
    #     sensor_key="Switchoff",
    #     unique_id="switchoff_reason",
    #     name="Switchoff Reason",
    #     icon="mdi:electric-switch",
    #     translation_key="switchoff_reason",
    #     unit_of_measurement=None,
    #     state_class=None,
    #     device_class=None,
    #     extra_value_attributes=["code"],
    # ),
    # LuxtronikIndexStatusSensor(
    #     key_index="calculations.ID_WEB_AnzahlFehlerInSpeicher",
    #     key_timestamp_template="calculations.ID_WEB_ERROR_Time0",
    #     luxtronik=luxtronik,
    #     device_info=device_info,
    #     sensor_key="calculations.ID_WEB_ERROR_Nr0",
    #     unique_id="error_reason",
    #     name="Error Reason",
    #     icon="mdi:alert",
    #     translation_key="error_reason",
    #     unit_of_measurement=None,
    #     state_class=None,
    #     device_class=None,
    #     extra_value_attributes=["code", "cause", "remedy"],
    # ),
    # endregion Main heatpump
    # region Heating
    LuxtronikSensorDescription(
        key="flow_out_temperature_target",
        luxtronik_key=LuxCalculation.C0012_FLOW_OUT_TEMPERATURE_TARGET,
        device_key=DeviceKey.heating,
        entity_category=None,
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    # endregion Heating
    # region Domestic water
    # LuxtronikSensorDescription(
    #     device_key=DeviceKey.domestic_water,
    #     luxtronik_key=LUX_PARAMETER_0004_MODE_DOMESTIC_WATER,
    #     key="domestic_water",
    #     icon="mdi:water-boiler-auto",
    #     icon_off="mdi:water-boiler-off",
    #     device_class=None,
    #     on_state=LuxMode.automatic.value,
    #     off_state=LuxMode.off.value,
    # ),
    # endregion Domestic water
    # region Cooling
    # LuxtronikSensorDescription(
    #     device_key=DeviceKey.cooling,
    #     luxtronik_key=LUX_PARAMETER_0108_MODE_COOLING,
    #     key="cooling",
    #     icon="mdi:snowflake",
    #     entity_category=EntityCategory.CONFIG,
    #     device_class=None,
    #     on_state=LuxMode.automatic.value,
    #     off_state=LuxMode.off.value,
    # ),
    # endregion Cooling
]
