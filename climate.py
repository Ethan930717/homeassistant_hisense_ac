import logging
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF, HVAC_MODE_COOL, HVAC_MODE_DRY, HVAC_MODE_FAN_ONLY, HVAC_MODE_HEAT,
    SUPPORT_FAN_MODE, SUPPORT_TARGET_TEMPERATURE)
from homeassistant.const import TEMP_CELSIUS, ATTR_TEMPERATURE

from .const import DOMAIN, FAN_MODE_HIGH, FAN_MODE_MEDIUM, FAN_MODE_LOW
from .hisense_api import get_status, control_ac

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = hass.data[DOMAIN][config_entry.entry_id]
    token = config["token"]
    home_id = config["home_id"]
    devices = config["devices"]
    status_list = get_status(token, home_id, devices)
    iu_map = map_iuIds_to_names(devices)

    entities = []
    for status in status_list:
        for iu_status in status['values']:
            iuId = iu_status.get('iuId')
            iuName = iu_map.get(iuId, '未知')
            entities.append(HisenseACClimate(token, home_id, iuName, iu_status, devices))

    async_add_entities(entities, True)


class HisenseACClimate(ClimateEntity):
    def __init__(self, token, home_id, name, status, devices):
        self._token = token
        self._home_id = home_id
        self._name = name
        self._status = status
        self._devices = devices
        self._device = next(
            (device for device in devices if any(iu['iuId'] == status['iuId'] for iu in device['iuList'])), None)

        self._hvac_mode = self._status.get('iu29Mode')
        self._fan_mode = self._status.get('iu30Wind')
        self._target_temperature = self._status.get('iu31Temp')
        self._onoff = self._status.get('iu28Onoff')

    @property
    def name(self):
        return self._name

    @property
    def hvac_mode(self):
        return self._hvac_mode

    @property
    def hvac_modes(self):
        return [HVAC_MODE_OFF, HVAC_MODE_COOL, HVAC_MODE_DRY, HVAC_MODE_FAN_ONLY, HVAC_MODE_HEAT]

    @property
    def fan_mode(self):
        return self._fan_mode

    @property
    def fan_modes(self):
        return [FAN_MODE_HIGH, FAN_MODE_MEDIUM, FAN_MODE_LOW]

    @property
    def temperature_unit(self):
        return TEMP_CELSIUS

    @property
    def target_temperature(self):
        return self._target_temperature

    @property
    def supported_features(self):
        return SUPPORT_FAN_MODE | SUPPORT_TARGET_TEMPERATURE

    @property
    def is_on(self):
        return self._onoff == 1

    async def async_set_hvac_mode(self, hvac_mode):
        await self.hass.async_add_executor_job(control_ac, self._token, self._home_id, self._device,
                                               hvac_mode=hvac_mode)
        self._hvac_mode = hvac_mode

    async def async_set_fan_mode(self, fan_mode):
        await self.hass.async_add_executor_job(control_ac, self._token, self._home_id, self._device, fan_mode=fan_mode)
        self._fan_mode = fan_mode
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            await self.hass.async_add_executor_job(control_ac, self._token, self._home_id, self._device,
                                                   temperature=temperature)
            self._target_temperature = temperature
            self.async_write_ha_state()

    async def async_turn_on(self):
        await self.async_set_hvac_mode(self._hvac_mode)
        self._onoff = 1
        self.async_write_ha_state()

    async def async_turn_off(self):
        await self.async_set_hvac_mode(HVAC_MODE_OFF)
        self._onoff = 0
        self.async_write_ha_state()