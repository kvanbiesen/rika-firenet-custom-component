import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (HVAC_MODE_AUTO,
                                                    HVAC_MODE_HEAT,
                                                    HVAC_MODE_OFF,
                                                    SUPPORT_PRESET_MODE,
                                                    SUPPORT_TARGET_TEMPERATURE,
                                                    PRESET_COMFORT,
                                                    PRESET_NONE,
                                                    CURRENT_HVAC_OFF,
                                                    CURRENT_HVAC_IDLE,
                                                    CURRENT_HVAC_HEAT)
from homeassistant.const import (ATTR_TEMPERATURE, TEMP_CELSIUS)

from .const import (DOMAIN, SUPPORT_PRESET)
from .core import RikaFirenetCoordinator
from .entity import RikaFirenetEntity

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE

MIN_TEMP = 16
MAX_TEMP = 30

HVAC_MODES = [HVAC_MODE_AUTO, HVAC_MODE_HEAT, HVAC_MODE_OFF]


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up platform."""
    _LOGGER.info("setting up platform climate")
    coordinator: RikaFirenetCoordinator = hass.data[DOMAIN][entry.entry_id]

    stove_entities = []

    # Create stove sensors
    for stove in coordinator.get_stoves():
        stove_entities.append(RikaFirenetStoveClimate(entry, stove, coordinator))

    if stove_entities:
        async_add_entities(stove_entities, True)


class RikaFirenetStoveClimate(RikaFirenetEntity, ClimateEntity):

    @property
    def current_temperature(self):
        temp = self._stove.get_room_temperature()
        _LOGGER.info('current_temperature(): ' + str(temp))
        return temp

    @property
    def min_temp(self):
        return MIN_TEMP

    @property
    def max_temp(self):
        return MAX_TEMP

    @property
    def preset_modes(self):
        """Return a list of available preset modes."""
        return SUPPORT_PRESET

    @property
    def preset_mode(self):
        """Return the current preset mode, e.g., home, away, temp."""
        if self._stove.get_stove_operation_mode() is 2:
            return PRESET_COMFORT
        else:
            return PRESET_NONE

    def set_preset_mode(self, preset_mode):
        """Set new preset mode."""
        _LOGGER.info('preset mode : ' + str(preset_mode))
        if preset_mode == PRESET_COMFORT:
            _LOGGER.info("setting up PRESET COMFORT")
            self._stove.set_stove_operation_mode(2)
        else:
            _LOGGER.info("setting up PRESET NONE")

            if self._stove.is_stove_heating_times_on() == True:
                self._stove.set_stove_operation_mode(1)
            else:
                self._stove.set_stove_operation_mode(0)
        self.schedule_update_ha_state()

    @property
    def target_temperature(self):
        temp = self._stove.get_room_thermostat()
        return temp

    @property
    def target_temperature_step(self):
        return 1

    @property
    def hvac_mode(self):
        return self._stove.get_hvac_mode()

    @property
    def hvac_modes(self):
        return HVAC_MODES

    @property
    def hvac_action(self):
        """Return current operation ie. heat, cool, idle."""
        if self._stove.get_status_text() == "stove_off":
            return CURRENT_HVAC_OFF
        elif self._stove.get_status_text() == "standby":
            return CURRENT_HVAC_IDLE
        else:
            return CURRENT_HVAC_HEAT

    def set_hvac_mode(self, hvac_mode):
        _LOGGER.info('set_hvac_mode()): ' + str(hvac_mode))
        self._stove.set_hvac_mode(str(hvac_mode))
        self.schedule_update_ha_state()

    @property
    def supported_features(self):
        return SUPPORT_FLAGS

    @property
    def temperature_unit(self):
        return TEMP_CELSIUS

    def set_temperature(self, **kwargs):
        temperature = int(kwargs.get(ATTR_TEMPERATURE))
        _LOGGER.info('set_temperature(): ' + str(temperature))

        if kwargs.get(ATTR_TEMPERATURE) is None:
            return

        if not self._stove.is_stove_on():
            return

        # do nothing if HVAC is switched off
        self._stove.set_stove_temperature(temperature)
        self.schedule_update_ha_state()
