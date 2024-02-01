from rflib.chipcon_gollum import *

if __name__ == "__main__":
    d = PandwaRF()
    d.setModeIDLE()
    freq = d.doFreqFinder()
    print(f"Found frequency : {freq} Hz")
    d.setModeIDLE()
