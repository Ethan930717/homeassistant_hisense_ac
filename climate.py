import logging
from datetime import timedelta
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF, HVAC_MODE_COOL, HVAC_MODE_DRY, HVAC_MODE_FAN_ONLY, HVAC_MODE_HEAT,
    SUPPORT_FAN_MODE, SUPPORT_TARGET_TEMPERATURE)
from homeassistant.const import TEMP_CELSIUS, ATTR_TEMPERATURE
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity

from .const import DOMAIN, FAN_MODE_HIGH, FAN_MODE_MEDIUM, FAN_MODE_LOW, SCAN_INTERVAL
from .hisense_api import get_status, control_ac, map_iuIds_to_names

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    config = hass.data[DOMAIN][config_entry.entry_id]
    token = config["token"]
    home_id = config["home_id"]
    devices = config["devices"]
    status_list = await hass.async_add_executor_job(get_status, token, home_id, devices)
    iu_map = map_iuIds_to_names(devices)

    coordinator = HisenseDataUpdateCoordinator(hass, token, home_id, devices, iu_map)
    await coordinator.async_refresh()

    entities = []
    for status in status_list:
        for iu_status in status['values']:
            iuId = iu_status.get('iuId')
            iuName = iu_map.get(iuId, '未知')
            entities.append(HisenseACClimate(coordinator, iuName, iu_status))

    async_add_entities(entities, True)

class HisenseDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, token, home_id, devices, iu_map):
        self.token = token
        self.home_id = home_id
        self.devices = devices
        self.iu_map = iu_map
        super().__init__(
            hass,
            _LOGGER,
            name="Hisense AC",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        return await self.hass.async_add_executor_job(get_status, self.token, self.home_id, self.devices)

class HisenseACClimate(CoordinatorEntity, ClimateEntity):
    def __init__(self, coordinator, name, status):
        super().__init__(coordinator)
        self._name = name
        self._status = status
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
        await self.hass.async_add_executor_job(control_ac, self.coordinator.token, self.coordinator.home_id, self.coordinator.devices, hvac_mode=hvac_mode)
        self._hvac_mode = hvac_mode
        self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode):
        await self.hass.async_add_executor_job(control_ac, self.coordinator.token, self.coordinator.home_id, self.coordinator.devices, fan_mode=fan_mode)
        self._fan_mode = fan_mode
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is not None:
            await self.hass.async_add_executor_job(control_ac, self.coordinator.token, self.coordinator.home_id, self.coordinator.devices, temperature=temperature)
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

    @property
    def extra_state_attributes(self):
        return {
            "mode": {1: "Cool", 2: "Dry", 3: "Fan", 4: "Heat"}.get(self._hvac_mode, "UNKNOWN"),
            "wind": {1: "High", 2: "Medium", 3: "Low"}.get(self._fan_mode, "UNKNOWN"),
            "temp": self._target_temperature
        }
