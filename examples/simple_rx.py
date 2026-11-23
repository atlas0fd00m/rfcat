from rflib.chipcon_gollum import *
import time

if __name__ == "__main__":
    d = PandwaRF()
    FREQ = 433920000
    DATARATE = 2500
    d.setModeIDLE()
    d.rxSetup(FREQ, MOD_ASK_OOK, DATARATE)
    d.setAmpMode(RF_RX_POWER_AMPLIFIER_ACTION_ON)
    d.setModeRX()
    print("Please send some data...")
    time.sleep(5)
    print("Data received :")
    print(d.RFrecv())
    d.setModeIDLE()
    