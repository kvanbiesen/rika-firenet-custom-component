import logging
import time
from datetime import datetime, timedelta


import requests
from bs4 import BeautifulSoup
from homeassistant.components.climate.const import (HVAC_MODE_AUTO,
                                                    HVAC_MODE_HEAT,
                                                    HVAC_MODE_OFF)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class RikaFirenetCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, username, password, default_temperature, default_scan_interval, config_flow=False):
        self.hass = hass
        self._username = username
        self._password = password
        self._default_temperature = default_temperature
        self._default_scan_interval = timedelta(seconds=default_scan_interval)
        self._client = None
        self._stoves = None
        self._number_fail = 0
        self.platforms = []

        if not config_flow:
            super().__init__(
                hass,
                _LOGGER,
                name=DOMAIN,
                update_method=self.async_update_data,
                update_interval=timedelta(seconds=default_scan_interval)
            )

    async def async_update_data(self):
        try:
            await self.hass.async_add_executor_job(self.update)
        except Exception as exception:
            _LOGGER.info('Update failed to Rika Firenet')
            raise UpdateFailed(exception)

    def setup(self):
        _LOGGER.info("setup()")
        self._client = requests.session()
        self._stoves = self.setup_stoves()

    def get_stoves(self):
        return self._stoves

    def get_default_temperature(self):
        return self._default_temperature

    def get_number_fail(self):
        return self._number_fail

    def connect(self):
        if self.is_authenticated():
            return
        data = {
            'email': self._username,
            'password': self._password
        }
        postResponse = self._client.post('https://www.rika-firenet.com/web/login', data)
        if not ('/logout' in postResponse.text):
            raise Exception('Failed to connect with Rika Firenet')
        else:
            _LOGGER.info('Connected to Rika Firenet')

    def is_authenticated(self):
        if 'connect.sid' not in self._client.cookies:
            return False
        expiresIn = list(self._client.cookies)[0].expires
        epochNow = int(datetime.now().strftime('%s'))
        if expiresIn <= epochNow:
            return False
        return True

    def get_stove_state(self, id):
        self.connect()
        url = 'https://www.rika-firenet.com/api/client/' + id + '/status?nocache=' + str(int(time.time()))
        data = self._client.get(url, timeout=10).json()
        _LOGGER.debug('get_stove_state : ' + str(data))
        return data

    def setup_stoves(self):
        self.connect()
        stoves = []
        postResponse = self._client.get('https://www.rika-firenet.com/web/summary', timeout=10)
        soup = BeautifulSoup(postResponse.content, "html.parser")
        stoveList = soup.find("ul", {"id": "stoveList"})
        if stoveList is None:
            return stoves
        for stove in stoveList.findAll('li'):
            stoveLink = stove.find('a', href=True)
            stoveName = stoveLink.attrs['href'].rsplit('/', 1)[-1]
            stove = RikaFirenetStove(self, stoveName, stoveLink.text)
            _LOGGER.info("Found stove : {}".format(stove))
            stoves.append(stove)
        return stoves

    def update(self):
        _LOGGER.debug("Update by timeout reached")
        for stove in self._stoves:
            if stove._state != None and stove._NeedSend == True :
                stove._state = self.set_stove_controls(stove._id, stove.get_control_state())
            else:
                stove.sync_state()
#test
            # if stove._state['sensors']['statusMainState'] == 6 and stove.is_stove_on():
            if stove.get_main_state() == 6 and stove.is_stove_on():
                _LOGGER.debug('statusMainState=6 and OnOff=on')
                _LOGGER.debug('turning off')
                stove._state['controls']['onOff'] = False
                self.set_stove_controls(stove._id, stove.get_control_state())
                _LOGGER.debug('turning on')
                stove._state['controls']['onOff']= True
                self.set_stove_controls(stove._id, stove.get_control_state())

    def set_stove_controls(self, id, data):
        data2 =  self.get_stove_state(id)
        data['revision'] = str(data2['controls']['revision'])
        _LOGGER.debug("set_stove_control data: " + str(data))
        for counter in range(1, 11):
            _LOGGER.info('In progress.. ({}/10)'.format(counter))
            r = self._client.post('https://www.rika-firenet.com/api/client/' + id + '/controls', data)
            if ('OK' in r.text) == True:
                _LOGGER.info('Stove controls updated')
                self._number_fail = 0
                self._NeedSend = False
                return self.get_stove_state(id)
            else:
                _LOGGER.debug('no send :' + str(data['revision']) + str(r.text))
                self._number_fail += 1
                time.sleep(5)
                data2 = self.get_stove_state(id)
                data['revision'] = str(data2['controls']['revision'])
        _LOGGER.info('Error, data not sended')
        return data



class RikaFirenetStove:

    def __init__(self, coordinator: RikaFirenetCoordinator, id, name):
        self._coordinator = coordinator
        self._id = id
        self._name = name
        self._previous_temperature = None
        self._state = None
        self._number_fail = 0
        self._NeedSend = False

    def get_number_fail(self):
        return self._number_fail

    def __repr__(self):
        return {'id': self._id, 'name': self._name}

    def __str__(self):
        return 'Stove(id=' + self._id + ', name=' + self._name + ')'

    def sync_state(self):
        _LOGGER.debug("Updating stove %s", self._id)
        self._state = self._coordinator.get_stove_state(self._id)
        self._number_fail = self._coordinator.get_number_fail()

#Send command

    def set_temperatureOffset(self, temperature):
        _LOGGER.debug("set_offset_temperature(): " + str(temperature))
        self._state['controls']['temperatureOffset'] = temperature
        self._NeedSend = True

    def set_stove_temperature(self, temperature):
        _LOGGER.debug("set_stove_temperature(): " + str(temperature))
        self._state['controls']['targetTemperature'] = temperature
        self._NeedSend = True

    def set_stove_set_back_temperature(self, temperature):
        _LOGGER.debug("set_back_temperature(): " + str(temperature))
        self._state['controls']['setBackTemperature'] = temperature
        self._NeedSend = True

    def set_stove_operation_mode(self, mode):
        _LOGGER.debug("set_stove_operation_mode(): " + str(mode))
        self._state['controls']['operatingMode'] = mode
        self._NeedSend = True

    def set_heating_times_active_for_comfort(self, active):
        _LOGGER.debug("set_heating_times_active_for_comfort(): " + str(active))
        self._state['controls']['onOff'] = True
        self._state['controls']['heatingTimesActiveForComfort'] = active
        self._NeedSend = True

    def set_room_power_request(self, power):
        _LOGGER.debug("set_room_power_request(): " + str(power))
        self._state['controls']['RoomPowerRequest'] = power
        self._NeedSend = True

    def set_heating_power(self, power):
        _LOGGER.debug("set_heating_power(): " + str(power))
        self._state['controls']['heatingPower'] = power
        self._NeedSend = True

    def set_convection_fan1_level(self, level):
        _LOGGER.debug("set_convection_fan1_level(): " + str(level))
        self._state['controls']['convectionFan1Level'] = level
        self._NeedSend = True

    def set_convection_fan1_area(self, area):
        _LOGGER.debug("set_convection_fan1_area(): " + str(area))
        self._state['controls']['convectionFan1Area'] = area
        self._NeedSend = True

    def set_convection_fan2_level(self, level):
        _LOGGER.debug("set_convection_fan2_level(): " + str(level))
        self._state['controls']['convectionFan2Level'] = level
        self._NeedSend = True

    def set_convection_fan2_area(self, area):
        _LOGGER.debug("set_convection_fan2_area(): " + str(area))
        self._state['controls']['convectionFan2Area'] = area
        self._NeedSend = True

    def turn_on_off(self, on_off=True):
        _LOGGER.debug("turn_off(): " + str(on_off))
        self._state['controls']['onOff'] = on_off
        self._NeedSend = True

    def turn_heating_times_on(self): 
        self._state['controls']['onOff'] = True
        self._state['controls']['heatingTimesActiveForComfort'] = True
        if not self.get_stove_operation_mode() == 2:
            self._state['controls']['operatingMode'] = int(1)
        self._NeedSend = True

    def turn_heating_times_off(self):
        self._state['controls']['onOff'] = True
        self._state['controls']['heatingTimesActiveForComfort'] = False
        if not self.get_stove_operation_mode() == 2:
            self._state['controls']['operatingMode'] = int(0)
        self._NeedSend = True

    def turn_convection_fan1_on_off(self, on_off=True):
        _LOGGER.debug("turn_convection_fan1_on_off(): " + str(on_off))
        self._state['controls']['convectionFan1Active'] = on_off
        self._NeedSend = True

    def turn_convection_fan2_on_off(self, on_off=True):
        _LOGGER.debug("turn_convection_fan2_on_off(): " + str(on_off))
        self._state['controls']['convectionFan2Active'] = on_off
        self._NeedSend = True

    def turn_on_off_eco_mode(self, on_off=False):
        _LOGGER.info("Set Eco Mode: " + str(on_off))
        self._state['controls']['ecoMode'] = on_off
        self._NeedSend = True

#End

    def get_id(self):
        return self._id

    def get_name(self):
        return self._name

    def get_control_state(self):
        return self._state['controls']

    def get_state(self):
        return self._state

    def get_room_temperature(self):
        return float(self._state['sensors']['inputRoomTemperature'])

    def get_temperatureOffset(self):
        return float(self._state['controls']['temperatureOffset'])

    def get_room_thermostat(self):
        return float(self._state['controls']['targetTemperature'])

    def is_stove_eco_mode(self):
        return bool(self._state['controls']['ecoMode'])

    def get_stove_set_back_temperature(self):
        return float(self._state['controls']['setBackTemperature'])

    def is_stove_on(self):
        return bool(self._state['controls']['onOff'])

    def turn_on(self):
        self.turn_on_off(True)

    def turn_off(self):
        self.turn_on_off(False)

    def get_stove_operation_mode(self):
        return self._state['controls']['operatingMode']

    def get_hvac_mode(self):
        if not self.is_stove_on():
            return HVAC_MODE_OFF
        elif self.is_stove_heating_times_on() == True:
            return HVAC_MODE_AUTO    
        elif self.is_stove_heating_times_on() == False: 
            return HVAC_MODE_HEAT

    def is_stove_heating_times_on(self):
        if self.get_stove_operation_mode() == 2:
            if not self.is_heating_times_active_for_comfort():
                return False
            else:
                return True
        elif self.get_stove_operation_mode() == 0:
            return False
        elif self.get_stove_operation_mode() == 1:
            return True

    def is_heating_times_active_for_comfort(self):
        return self._state['controls']['heatingTimesActiveForComfort']

    def get_room_power_request(self):
        return int(self._state['controls']['RoomPowerRequest'])

    def get_heating_power(self):
        return int(self._state['controls']['heatingPower'])

    def is_stove_convection_fan1_on(self):
        return bool(self._state['controls']['convectionFan1Active'])

    def set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVAC_MODE_OFF:
            self.turn_off()
        elif hvac_mode == HVAC_MODE_AUTO:
            _LOGGER.debug("Turn heating times on")
            self.turn_heating_times_on()
        elif hvac_mode == HVAC_MODE_HEAT:
            _LOGGER.debug("Turn heating times off")
            self.turn_heating_times_off()

    def turn_on_eco_mode(self):
        self.turn_on_off_eco_mode(True)

    def turn_off_eco_mode(self):
        self.turn_on_off_eco_mode(False)

    def turn_convection_fan1_on(self):
        self.turn_convection_fan1_on_off(True)

    def turn_convection_fan1_off(self):
        self.turn_convection_fan1_on_off(False)

    def get_convection_fan1_level(self):
        return int(self._state['controls']['convectionFan1Level'])

    def get_convection_fan1_area(self):
        return int(self._state['controls']['convectionFan1Area'])

    def is_stove_convection_fan2_on(self):
        return bool(self._state['controls']['convectionFan2Active'])

    def turn_convection_fan2_on(self):
        self.turn_convection_fan2_on_off(True)

    def turn_convection_fan2_off(self):
        self.turn_convection_fan2_on_off(False)

    def get_convection_fan2_level(self):
        return int(self._state['controls']['convectionFan2Level'])

    def get_convection_fan2_area(self):
        return int(self._state['controls']['convectionFan2Area'])

    def is_stove_burning(self):
        if self.get_main_state() == 4 or self.get_main_state() == 5:
            return True
        else:
            return False

    def get_stove_consumption(self):
        return self._state['sensors']['parameterFeedRateTotal']

    def get_stove_runtime(self):
        return self._state['sensors']['parameterRuntimePellets']

    def get_pellets_before_service(self):
        return self._state['sensors']['parameterFeedRateService']

    def get_stove_temperature(self):
        return float(self._state['sensors']['inputFlameTemperature'])

    def get_diag_motor(self):
        return self._state['sensors']['outputDischargeMotor']

    def get_fan_velocity(self):
        return self._state['sensors']['outputIDFan']

    def get_status_text(self):
        return self.get_status()[1]

    def get_status_picture(self):
        return self.get_status()[0]

    def get_main_state(self):
        return self._state['sensors']['statusMainState']

    def get_sub_state(self):
        return self._state['sensors']['statusSubState']

    def get_status(self):
        main_state = self.get_main_state()
        sub_state = self.get_sub_state()
        frost_started = bool(self._state['sensors']['statusFrostStarted'])
        statusError = int(self._state['sensors']['statusError'])
        statusSubError = int(self._state['sensors']['statusSubError'])
        lastSeenMinutes = int(self._state['lastSeenMinutes'])



# DEBUG for errors
        if lastSeenMinutes != 0:
            _LOGGER.debug("lastSeenMinutes: " + str(lastSeenMinutes))
        if statusError != 0:
            _LOGGER.debug("statusError: " + str(statusError))
        if statusSubError != 0:
            _LOGGER.debug("statusSubError: " + str(statusSubError))
        if lastSeenMinutes > 2:
            return ["https://www.rika-firenet.com/images/status/Warning_WifiSignal.svg", "offline"]
        if statusError == 1:
            if statusSubError == 1:
                return ["/", "Error 1"]
            elif statusSubError == 2:
                return ["https://raw.githubusercontent.com/antibill51/rika-firenet-custom-component/main/images/status/Visu_Empty.svg", "empty_tank"]
            return ["/", "statusSubError" + str(statusSubError)]
        if frost_started:
            return ["https://www.rika-firenet.com/images/status/Visu_Freeze.svg", "frost_protection"]
        if main_state == 1:
            if sub_state == 0:
                return ["https://www.rika-firenet.com/images/status/Visu_Off.svg", "stove_off"]
            elif sub_state == 1:
                return ["https://www.rika-firenet.com/images/status/Visu_Standby.svg", "standby"]
            elif sub_state == 2:
                return ["https://www.rika-firenet.com/images/status/Visu_Standby.svg", "external_request"]
            elif sub_state == 3:
                return ["https://www.rika-firenet.com/images/status/Visu_Standby.svg", "standby"]
            return ["https://www.rika-firenet.com/images/status/Visu_Off.svg", "sub_state_unknown"]
        elif main_state == 2:
            return ["https://www.rika-firenet.com/images/status/Visu_Ignition.svg", "ignition_on"]
        elif main_state == 3:
            return ["https://www.rika-firenet.com/images/status/Visu_Ignition.svg", "starting_up"]
        elif main_state == 4:
            return ["https://www.rika-firenet.com/images/status/Visu_Control.svg", "running"]
        elif main_state == 5:
            if sub_state == 3 or sub_state == 4:
                return ["https://www.rika-firenet.com/images/status/Visu_Clean.svg", "big_clean"]
            else:
                return ["https://www.rika-firenet.com/images/status/Visu_Clean.svg", "clean"]
        elif main_state == 6:
            return ["https://www.rika-firenet.com/images/status/Visu_BurnOff.svg", "burn_off"]
        elif main_state == 11 or main_state == 13 or main_state == 14 or main_state == 16 or main_state == 17 or main_state == 50:
            return ["/images/status/Visu_SpliLog.svg", "split_log_check"]
        elif main_state == 21 and sub_state == 12 and stove_temp <=350 and stove_temp >= 300:
            return ["/images/status/Visu_SpliLog.svg", "split_log_refuel"]
        elif main_state == 21 and sub_state == 12 and stove_temp < 300:
            return ["/images/status/Visu_SpliLog.svg", "split_log_stop_refuel"]
        elif main_state == 20 or main_state == 21:
            return ["https://www.rika-firenet.com/images/status/Visu_SpliLog.svg", "split_log_mode"]
        return ["https://www.rika-firenet.com/images/status/Visu_Off.svg", "unknown"]
