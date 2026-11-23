from rflib.chipcon_gollum import *

if __name__ == "__main__":
    d = PandwaRF()
    d.setModeIDLE()
    FREQ = 433_920_000
    DATARATE = 10_000 # Equivalent to spectrum wideness of the jamming
    d.doJamming(FREQ, DATARATE)
    d.setModeIDLE()
