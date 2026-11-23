from rflib.chipcon_gollum import *

if __name__ == "__main__":
    d = PandwaRF()
    d.setModeIDLE()
    FREQ = 433920000
    d.doDataRateDetect(FREQ, MOD_ASK_OOK)
    d.setModeIDLE()
