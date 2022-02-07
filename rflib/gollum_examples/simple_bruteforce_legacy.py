from rflib.chipcon_gollum import *

if __name__ == "__main__":
    # If you have a PandwaRF Rogue, it is better to use the
    # other version of bruteforce (non-legacy)
    d = PandwaRF()
    d.setModeIDLE()
    FREQ = 433_890_000
    DATARATE = 5_320
    MOD = MOD_ASK_OOK
    codeLength = 8
    startValue = 0
    stopValue = 6560
    repeat = 10
    delayMs = 0x64

    encSymbolZero = 0x8E
    encSymbolOne = 0xEE
    encSymbolTwo = 0xE8
    encSymbolThree = 0x00
    syncWordSize = 2
    syncWord = 0x0008

    functionSize = 8
    functionMask = 0xFFFFFF0000FFFFFF
    functionValue= 0x000000EEE8000000

    d.doBruteForceLegacy(FREQ, MOD, DATARATE, startValue, stopValue, codeLength, repeat, delayMs, encSymbolZero, encSymbolOne, encSymbolTwo, encSymbolThree, syncWordSize, syncWord, functionSize, functionMask, functionValue)

    d.setModeIDLE()