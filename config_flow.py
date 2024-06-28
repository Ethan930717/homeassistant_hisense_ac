import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .token_store import save_token
from .hisense_api import try_login, get_device_list

_LOGGER = logging.getLogger(__name__)

@callback
def configured_instances(hass):
    return [entry.entry_id for entry in hass.config_entries.async_entries(DOMAIN)]

class HisenseACConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            phone_no = user_input["phone_no"]
            password = user_input["password"]
            _LOGGER.debug("User input received: phone_no=%s", phone_no)

            try:
                token, home_id, error = await self.hass.async_add_executor_job(
                    try_login, phone_no, password
                )

                if token:
                    _LOGGER.debug("Login successful: token=%s, home_id=%s", token, home_id)
                    save_token(self.hass, token, home_id)
                    return await self.async_step_select_device()
                else:
                    _LOGGER.error("Login failed: %s", error)
                    errors["base"] = error or "unknown_error"
            except Exception as e:
                _LOGGER.exception("Unexpected exception during login")
                errors["base"] = str(e)

        data_schema = vol.Schema({
            vol.Required("phone_no"): str,
            vol.Required("password"): str
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_select_device(self, user_input=None):
        errors = {}
        token_data = load_token(self.hass)

        if user_input is not None:
            selected_devices = user_input["devices"]
            self.hass.data[DOMAIN]["selected_devices"] = selected_devices
            return self.async_create_entry(
                title="Hisense AC",
                data={"selected_devices": selected_devices}
            )

        devices = await self.hass.async_add_executor_job(
            get_device_list, token_data["token"], token_data["home_id"]
        )

        device_dict = {device["name"]: device["id"] for device in devices}

        data_schema = vol.Schema({
            vol.Required("devices"): cv.multi_select(device_dict)
        })

        return self.async_show_form(
            step_id="select_device", data_schema=data_schema, errors=errors
        )
