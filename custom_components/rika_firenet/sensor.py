import logging

from homeassistant.const import UnitOfTemperature, UnitOfTime, UnitOfMass, PERCENTAGE
from .entity import RikaFirenetEntity
from homeassistant.helpers.entity import EntityCategory
from .const import (
    DOMAIN
)
from .core import RikaFirenetCoordinator
from .core import RikaFirenetStove

_LOGGER = logging.getLogger(__name__)

DEVICE_SENSORS = [
    "stove_consumption",
    "stove_runtime",
    "stove_temperature",
    "room_temperature",
    "stove_thermostat",
    "stove_burning",
    "stove_status",
    "pellets_before_service",
    "fan_velocity",
    "diag_motor",
    "number_fail",
    "main_state",
    "sub_state",
    "statusError",
    "statusSubError"
]


async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.info("setting up platform sensor")
    coordinator: RikaFirenetCoordinator = hass.data[DOMAIN][entry.entry_id]

    stove_entities = []

    # Create stove sensors
    for stove in coordinator.get_stoves():
        stove_entities.extend(
            [
                RikaFirenetStoveSensor(entry, stove, coordinator, sensor)
                for sensor in DEVICE_SENSORS
            ]
        )

    if stove_entities:
        async_add_entities(stove_entities, True)


class RikaFirenetStoveSensor(RikaFirenetEntity):
    def __init__(self, config_entry, stove: RikaFirenetStove, coordinator: RikaFirenetCoordinator, sensor):
        super().__init__(config_entry, stove, coordinator, sensor)
        self._sensor = sensor

    @property
    def state(self):
        if self._sensor == "stove_consumption":
            return self._stove.get_stove_consumption()
        elif self._sensor == "stove_runtime":
            return self._stove.get_stove_runtime()
        elif self._sensor == "stove_temperature":
            return self._stove.get_stove_temperature()
        elif self._sensor == "room_temperature":
            return self._stove.get_room_temperature()
        elif self._sensor == "stove_thermostat":
            return self._stove.get_room_thermostat()
        elif self._sensor == "stove_burning":
            return self._stove.is_stove_burning()
        elif self._sensor == "stove_status":
            return self._stove.get_status_text()
        elif self._sensor == "pellets_before_service":
            return self._stove.get_pellets_before_service()
        elif self._sensor == "diag_motor":
            return self._stove.get_diag_motor()
        elif self._sensor == "fan_velocity":
            return self._stove.get_fan_velocity()
        elif self._sensor == "number_fail":
            return self._stove.get_number_fail()
        elif self._sensor == "main_state":
            return self._stove.get_main_state()
        elif self._sensor == "sub_state":
            return self._stove.get_sub_state()
        elif self._sensor == "statusError" :
            return self._stove.get_status_error()
        elif self._sensor == "statusSubError":
            return self._stove.get_status_sub_error()


    @property
    def unit_of_measurement(self):
        if "temperature" in self._sensor or "thermostat" in self._sensor:
            return UnitOfTemperature.CELSIUS
        elif self._sensor == "stove_consumption" or self._sensor == "pellets_before_service":
            return UnitOfMass.KILOGRAMS
        elif self._sensor == "stove_runtime":
            return UnitOfTime.HOURS


    @property
    def icon(self):
        if "temperature" in self._sensor or "thermostat" in self._sensor:
            return "mdi:thermometer"
        elif self._sensor == "stove_consumption" or self._sensor == "pellets_before_service":
            return "mdi:weight-kilogram"
        elif self._sensor == "stove_runtime":
            return "mdi:timer-outline"
        elif self._sensor == "stove_burning":
            return "mdi:fire"
        elif self._sensor == "stove_status" or self._sensor == "number_fail" or self._sensor == "main_state" or self._sensor == "sub_state":
            return "mdi:information-outline"
        elif self._sensor == "diag_motor" or self._sensor == "fan_velocity":
            return "mdi:speedometer"


    @property
    def entity_category(self):
        if self._sensor == "stove_consumption":
            return EntityCategory.DIAGNOSTIC
        elif self._sensor == "stove_runtime":
            return EntityCategory.DIAGNOSTIC
        elif self._sensor == "stove_temperature":
            return EntityCategory.DIAGNOSTIC
        elif self._sensor == "stove_burning":
            return EntityCategory.DIAGNOSTIC
        elif self._sensor == "pellets_before_service":
            return EntityCategory.DIAGNOSTIC
        elif self._sensor == "diag_motor":
            return EntityCategory.DIAGNOSTIC 
        elif self._sensor == "fan_velocity":
            return EntityCategory.DIAGNOSTIC 
        elif self._sensor == "number_fail":
            return EntityCategory.DIAGNOSTIC 
        elif self._sensor == "main_state":
            return EntityCategory.DIAGNOSTIC 
        elif self._sensor == "sub_state":
            return EntityCategory.DIAGNOSTIC 
        elif self._sensor == "statusError" :
            return EntityCategory.DIAGNOSTIC 
        elif self._sensor == "statusSubError":
            return EntityCategory.DIAGNOSTIC 


    @property
    def translation_key(self):
        return self._sensor