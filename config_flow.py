import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from .const import DOMAIN
from .hisense_api import try_login, get_device_list, save_data

class HisenseACConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            try:
                token, home_id = await self.hass.async_add_executor_job(try_login, user_input["phone_no"], user_input["password"])
                if token:
                    home_detail, devices = await self.hass.async_add_executor_job(get_device_list, token, home_id)
                    await self.hass.async_add_executor_job(save_data, home_detail, devices)
                    return self.async_create_entry(title="Hisense AC", data={"token": token, "home_id": home_id, "devices": devices})
                else:
                    errors = {"base": "auth"}
                    return self.async_show_form(step_id="user", data_schema=self._get_schema(), errors=errors)
            except Exception as e:
                _LOGGER.error(f"Error during login: {e}")
                errors = {"base": "auth"}
                return self.async_show_form(step_id="user", data_schema=self._get_schema(), errors=errors)

        return self.async_show_form(step_id="user", data_schema=self._get_schema())

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HisenseACOptionsFlowHandler(config_entry)

    def _get_schema(self):
        return vol.Schema({
            vol.Required("phone_no"): str,
            vol.Required("password"): str
        })

class HisenseACOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return self.async_show_form(step_id="init", data_schema=vol.Schema({}))
