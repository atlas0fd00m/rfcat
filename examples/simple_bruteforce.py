from rflib.chipcon_gollum import *

if __name__ == "__main__":
    # This bruteforce is only available on PandwaRF Rogue
    # See bruteforce legacy for the PandwaRF (non Rogue)
    d = PandwaRFRogue()
    d.setModeIDLE()
    FREQ = 433_920_000
    DATARATE = 24_536
    MOD = MOD_ASK_OOK
    codeLength = 12
    startValue = 3190
    stopValue = 3300
    repeat = 6
    delayMs = 30

    symbolLength = 3
    encSymbolZero = 0xFF0000
    encSymbolOne = 0xFF00FF
    encSymbolTwo = 0x000000
    encSymbolThree = 0x000000
    syncWordSize = 40
    syncWord = 0
    tailWordSize = 8
    tailWord = 0xFF00000000000000
    functionSize = 12
    functionMask = 0xFFFFFFFFFFFFFFFFFFFF0000
    functionValue= 0x000000000000000000000001

    d.doBruteForce(FREQ, MOD, DATARATE, startValue, stopValue, codeLength, repeat, delayMs, symbolLength, encSymbolZero, encSymbolOne, encSymbolTwo, encSymbolThree, syncWordSize, syncWord, tailWordSize, tailWord, functionSize, functionMask, functionValue)

    d.setModeIDLE()