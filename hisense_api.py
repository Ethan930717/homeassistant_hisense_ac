import requests
import logging

from .const import LOGIN_URL, HOME_URL, STATUS_URL, CONTROL_URL, HEADERS

_LOGGER = logging.getLogger(__name__)

def try_login(phone_no, password):
    headers = HEADERS
    payload = {
        "phoneNo": phone_no,
        "password": password,
        "jgRegId": "13165ffa4eec171534e",
        "version": 0
    }

    response = requests.post(LOGIN_URL, headers=headers, json=payload)
    _LOGGER.debug(f"Login response: {response.status_code} - {response.text}")

    if response.status_code == 200:
        data = response.json()
        if data["code"] == "200":
            token = data["data"]["user"]["token"]
            home_id = data["data"]["user"]["defaultHomeId"]
            return token, home_id, None
        else:
            return None, None, data["message"]
    else:
        return None, None, f"Request failed, status code: {response.status_code}"

def get_device_list(token, home_id):
    url = f"{HOME_URL}/{home_id}"
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    response = requests.get(url, headers=headers)

    _LOGGER.debug(f"Get device list response: {response.status_code} - {response.text}")

    if response.status_code == 200:
        data = response.json()
        if data["code"] == "200":
            home_detail = data["data"]["homeDetail"]
            device_list = home_detail.get("deviceList", [])
            return device_list
        else:
            _LOGGER.error("Failed to get home and device info: %s", data["message"])
    else:
        _LOGGER.error("Request failed, status code: %s", response.status_code)

    return []

def get_status(token, home_id, device):
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    payload = {
        "iuIdList": [{
            "iezCode": device["iezCode"],
            "iuIds": [{"iuId": device["iuId"], "timestamp": 0}]
        }],
        "plcList": [],
        "boxList": [],
        "xkqListGjy": [],
        "iuIdListGjy": [],
        "noNetTip": True
    }
    _LOGGER.debug(f"Getting status for {device['name']} with payload: {payload}")
    response = requests.post(STATUS_URL.format(home_id=home_id), headers=headers, json=payload)
    _LOGGER.debug(f"Get status response: {response.status_code} - {response.text}")

    if response.status_code == 200:
        data = response.json()
        status_list = data.get("data", {}).get("statusList", [])
        if status_list:
            return status_list[0]
    _LOGGER.error(f"Failed to get status for {device['name']}: {response.status_code} - {response.text}")
    return None

def control_ac(token, home_id, device, temperature=None, hvac_mode=None, fan_mode=None):
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    ctrl_json = {}
    if hvac_mode is not None:
        ctrl_json["onoff"] = 1 if hvac_mode != HVAC_MODE_OFF else 0
        ctrl_json["mode"] = map_mode_to_api(hvac_mode)
    if temperature is not None:
        ctrl_json["temp"] = temperature
    if fan_mode is not None:
        ctrl_json["wind"] = map_fan_mode_to_api(fan_mode)

    payload = {
        "ctrlList": [{
            "iuCtrlInfo": [{
                "iuNo": "00",
                "systemNo": "00",
                "iuSn": device["iuId"],
                "iuType": "09",
                "ctrlJson": ctrl_json
            }],
            "plcCtrlInfo": [],
            "iezCode": device["iezCode"],
            "deviceType": "1",
            "versionModbusProtocol": 0,
            "plcGatewayMac": "0"
        }],
        "homeId": home_id,
        "ctrlType": "HI420",
        "regionCode": "110101",
        "positionLng": 116.397128,
        "positionLat": 39.904202,
        "position1": "北京市 北京市 东城区",
        "position2": "天安门",
        "positionCity": "北京市"
    }

    _LOGGER.debug(f"Sending control command to {device['name']} with payload: {payload}")
    response = requests.post(CONTROL_URL, headers=headers, json=payload)
    _LOGGER.debug(f"Control response: {response.status_code} - {response.text}")

    if response.status_code != 200:
        _LOGGER.error(f"Failed to control AC {device['name']}: {response.status_code} - {response.text}")

    if response.status_code == 200:
        _LOGGER.info(f"Successfully controlled AC {device['name']}")
    else:
        _LOGGER.error(f"Failed to control AC {device['name']}")

def map_mode_to_api(hvac_mode):
    return {
        HVAC_MODE_COOL: 1,
        HVAC_MODE_DRY: 2,
        HVAC_MODE_FAN_ONLY: 3,
        HVAC_MODE_HEAT: 4,
        HVAC_MODE_OFF: 0
    }.get(hvac_mode, 0)

def map_fan_mode_to_api(fan_mode):
    return {
        FAN_MODE_HIGH: 1,
        FAN_MODE_MEDIUM: 2,
        FAN_MODE_LOW: 3
    }.get(fan_mode, 3)
