import json
from rflib.chipcon_gollum import *
import time, requests

if __name__ == "__main__":
    d = PandwaRF()
    FREQ = 433_920_000
    DATARATE = 10_000
    # Your token can be found on https://rolling.pandwarf.com/profile-user
    # It is the 'API token'
    KAIJU_API_TOKEN = "YOUR_KAIJU_API_TOKEN_HERE"

    d.setModeIDLE()
    d.rxSetup(FREQ, MOD_ASK_OOK, DATARATE)
    d.setAmpMode(RF_RX_POWER_AMPLIFIER_ACTION_ON)
    d.setModeRX()
    print("Please send some data...")
    time.sleep(5)
    data, _ = d.RFrecv()
    print(f"Data received : {data.hex()}")
    d.setModeIDLE()
    print("Analysing data with Kaiju...")

    base_url = "https://rolling.pandwarf.com/api/v1"
    s = requests.Session()
    s.headers.update({
        'Authorization': f'Token {KAIJU_API_TOKEN}'
    })

    payload = {
        "rawHexStream": data.hex()
    }
    payload = json.dumps(payload)
    response = s.post(f"{base_url}/analyze/detailed", data=payload)

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

    print("Processing done, now retrieving the result :")
    r = s.get(f"{base_url}/remote/{taskId}")
    result = r.json()
    remoteData = result["remoteData"]
    print(json.dumps(remoteData, indent=2))
