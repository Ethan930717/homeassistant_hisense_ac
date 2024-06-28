import logging
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    SUPPORT_TARGET_TEMPERATURE
)
from homeassistant.const import TEMP_CELSIUS
from .const import CONTROL_ENDPOINT, HEADERS, DOMAIN
from .hisense_api import get_status, control_ac

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    _LOGGER.debug("Setting up climate platform")
    coordinator = hass.data[DOMAIN]["coordinator"]
    devices = coordinator.data

    entities = []
    for device in devices:
        entities.append(HisenseAC(coordinator, device))
    async_add_entities(entities)

class HisenseAC(ClimateEntity):
    def __init__(self, coordinator, device):
        self.coordinator = coordinator
        self.device = device
        self._name = device["name"]
        self._unique_id = device["id"]
        self._state = HVAC_MODE_OFF
        self._temperature = None
        _LOGGER.debug("Initialized Hisense AC: %s", self._name)

    @property
    def supported_features(self):
        return SUPPORT_TARGET_TEMPERATURE

    @property
    def hvac_modes(self):
        return [HVAC_MODE_OFF, HVAC_MODE_COOL, HVAC_MODE_HEAT]

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def temperature_unit(self):
        return TEMP_CELSIUS

    @property
    def target_temperature(self):
        return self._temperature

    async def async_set_hvac_mode(self, hvac_mode):
        token_data = self.coordinator.hass.data[DOMAIN].get("token_data")
        result = await self.coordinator.hass.async_add_executor_job(
            control_ac, token_data["token"], token_data["home_id"], self.device, hvac_mode=hvac_mode
        )
        if result:
            self._state = hvac_mode
            self.async_write_ha_state()

    async def async_update(self):
        _LOGGER.debug("Updating Hisense AC: %s", self._name)
        token_data = self.coordinator.hass.data[DOMAIN].get("token_data")
        status = await self.coordinator.hass.async_add_executor_job(
            get_status, token_data["token"], token_data["home_id"], self.device
        )
        if status:
            _LOGGER.info(f"Status for {self._name}: {status}")
            values = status.get('values', [])
            if values:
                value = values[0]
                _LOGGER.debug(f"Device status value: {value}")
                self._state = value.get("iu28Onoff")
                self._temperature = value.get("iu31Temp")
                self._hvac_mode = self.map_hvac_mode(value.get("iu29Mode"))
                self._fan_mode = self.map_fan_mode(value.get("iu30Wind"))

    def map_hvac_mode(self, hvac_mode):
        return {
            0: HVAC_MODE_OFF,
            1: HVAC_MODE_COOL,
            2: HVAC_MODE_DRY,
            3: HVAC_MODE_FAN_ONLY,
            4: HVAC_MODE_HEAT
        }.get(hvac_mode, HVAC_MODE_OFF)

    def map_fan_mode(self, fan_mode):
        return {
            1: "high",
            2: "medium",
            3: "low"
        }.get(fan_mode, "low")
