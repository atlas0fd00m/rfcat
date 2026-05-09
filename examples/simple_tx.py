from rflib.chipcon_gollum import *

if __name__ == "__main__":
    d = PandwaRF()
    FREQ = 433920000
    DATARATE = 2500
    d.setModeIDLE()
    d.txSetup(FREQ, MOD_ASK_OOK, DATARATE)
    d.setAmpMode(RF_TX_POWER_AMPLIFIER_ACTION_ON)
    d.setModeTX()
    d.RFxmit(b"HALLO")
    d.setModeIDLE()
