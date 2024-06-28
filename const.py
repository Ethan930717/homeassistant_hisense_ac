BASE_URL = "https://1app.hicloud.hisensehitachi.com"
LOGIN_URL = f"{BASE_URL}/login"
HOME_URL = f"{BASE_URL}/api/apphome/homes"
STATUS_URL = f"{BASE_URL}/api/appstatus/homes/{{home_id}}/status"
CONTROL_URL = f"{BASE_URL}/api/appcontrol/cmds/multiIuOuCtrl"
TOKEN_FILE = "hisense_token.json"

HEADERS = {
    'X-His-AppTag': 'V2',
    'X-His-APIKey': '1QiLCJhbGciOiJIUzI1NiF8',
    'X-His-AppId': 'com.hisensehitachi.himit2',
    'X-His-Version': '3.2.0_240422112513_release',
    'Content-Type': 'application/json'
}

# Define HVAC modes
HVAC_MODE_OFF = 0
HVAC_MODE_COOL = 1
HVAC_MODE_DRY = 2
HVAC_MODE_FAN_ONLY = 3
HVAC_MODE_HEAT = 4

# Define fan modes
FAN_MODE_HIGH = 1
FAN_MODE_MEDIUM = 2
FAN_MODE_LOW = 3
