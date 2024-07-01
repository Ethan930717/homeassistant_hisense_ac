DOMAIN = "hisense_ac"
DATA_FILE = "hisense_data.json"

# API Constants
BASE_URL = "https://1app.hicloud.hisensehitachi.com"
STATUS_URL = f"{BASE_URL}/api/appstatus/homes/{{home_id}}/status"
CONTROL_URL = f"{BASE_URL}/api/appcontrol/cmds/multiIuOuCtrl"
HEADERS = {
    'X-His-AppTag': 'V2',
    'X-His-APIKey': '1QiLCJhbGciOiJIUzI1NiF8',
    'X-His-AppId': 'com.hisensehitachi.himit2',
    'X-His-Version': '3.2.0_240422112513_release',
    'Content-Type': 'application/json'
}

# HVAC Modes
HVAC_MODE_OFF = 0
HVAC_MODE_COOL = 1
HVAC_MODE_DRY = 2
HVAC_MODE_FAN_ONLY = 3
HVAC_MODE_HEAT = 4

# Fan Modes
FAN_MODE_HIGH = 1
FAN_MODE_MEDIUM = 2
FAN_MODE_LOW = 3
