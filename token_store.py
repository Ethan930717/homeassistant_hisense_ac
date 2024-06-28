import json
import os
import logging

from homeassistant.helpers.storage import STORAGE_DIR

from .const import TOKEN_FILE

_LOGGER = logging.getLogger(__name__)

def save_token(hass, token, home_id):
    token_data = {
        "token": token,
        "home_id": home_id
    }
    path = os.path.join(hass.config.path(STORAGE_DIR), TOKEN_FILE)
    with open(path, 'w') as f:
        json.dump(token_data, f)
    _LOGGER.debug("Token saved: %s", token_data)

def load_token(hass):
    path = os.path.join(hass.config.path(STORAGE_DIR), TOKEN_FILE)
    if os.path.exists(path):
        with open(path, 'r') as f:
            token_data = json.load(f)
        _LOGGER.debug("Token loaded: %s", token_data)
        return token_data
    _LOGGER.warning("Token file not found")
    return None
