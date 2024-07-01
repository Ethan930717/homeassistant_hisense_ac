import requests
import logging
import json
from .const import BASE_URL, STATUS_URL, CONTROL_URL, HEADERS, DATA_FILE, HVAC_MODE_OFF, HVAC_MODE_COOL, HVAC_MODE_DRY, \
    HVAC_MODE_FAN_ONLY, HVAC_MODE_HEAT, FAN_MODE_HIGH, FAN_MODE_MEDIUM, FAN_MODE_LOW

_LOGGER = logging.getLogger(__name__)


def get_status(token, home_id, devices):
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"

    iuId_list = []
    for device in devices:
        for iu in device.get("iuList", []):
            iuId_list.append({
                "iuId": iu["iuId"],
                "timestamp": 0
            })

    payload = {
        "iuIdList": [{
            "iezCode": devices[0]["iezCode"],  # Assuming all devices have the same iezCode
            "iuIds": iuId_list
        }],
        "plcList": [],
        "boxList": [],
        "noNetTip": True
    }

    _LOGGER.debug(f"Getting status with payload: {payload}")
    response = requests.post(STATUS_URL.format(home_id=home_id), headers=headers, json=payload)
    _LOGGER.debug(f"Get status response: {response.status_code} - {response.text}")

    if response.status_code == 200:
        data = response.json()
        status_list = data.get("data", {}).get("statusList", [])
        return status_list
    _LOGGER.error(f"Failed to get status: {response.status_code} - {response.text}")
    return None


def control_ac(token, home_id, device, temperature=None, hvac_mode=None, fan_mode=None):
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {token}"
    ctrl_json = {}
    if hvac_mode is not None:
        ctrl_json["onoff"] = 1 if hvac_mode != HVAC_MODE_OFF else 0
        ctrl_json["mode"] = hvac_mode
    if temperature is not None:
        ctrl_json["temp"] = temperature
    if fan_mode is not None:
        ctrl_json["wind"] = fan_mode

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
    }

    _LOGGER.debug(f"Sending control command to {device['iuName']} with payload: {payload}")
    response = requests.post(CONTROL_URL, headers=headers, json=payload)
    _LOGGER.debug(f"Control response: {response.status_code} - {response.text}")

    if response.status_code != 200:
        _LOGGER.error(f"Failed to control AC {device['iuName']}: {response.status_code} - {response.text}")

    if response.status_code == 200:
        _LOGGER.info(f"Successfully controlled AC {device['iuName']}")
    else:
        _LOGGER.error(f"Failed to control AC {device['iuName']}")


def save_data(home_detail, devices):
    data = {
        "homeDetail": home_detail,
        "devices": devices
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    _LOGGER.info(f"Data saved to {DATA_FILE}")


def map_iuIds_to_names(devices):
    iu_map = {}
    for device in devices:
        for iu in device['iuList']:
            iu_map[iu['iuId']] = iu['iuName']
    return iu_map
