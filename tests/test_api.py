import os
import tempfile
import unittest
from rflib.fakedongle_nic import FakeRfCat


testhex = ''':10000000020102FFFFFFFFFFFFFFFFFFFFFFFFFFF8
:10001000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF0
:10002000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE0
:10003000FFFFFF022010FFFFFFFFFFFFFFFFFFFF9B
:10004000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC0
:10005000FFFFFF02164EFFFFFFFFFFFFFFFFFFFF47
:10006000FFFFFFFFFFFFFFFFFFFFFF022065FFFF16
:10007000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF90
:10FF4000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC1
:10FF5000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFB1
:10FF6000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFA1
:10FF7000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF91
:10FF8000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF81
:10FF9000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF71
:10FFA000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF61
:10FFB000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF51
:10FFC000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF41
:10FFD000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF31
:10FFE000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF21
:10FFF000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF11
:00000001FF
'''


class TestApis(unittest.TestCase):
    def __init__(self):
        self.d = FakeRfCat()

    def test_api_usb(self):
        self.assertEqual(self.d.getPartNum(), FAKE_PARTNUM)
        '''
rflib/chipcon_usb.py:35:def getRfCatDevices():
rflib/chipcon_usb.py:106:    def setRFparameters(self):
rflib/chipcon_usb.py:119:    def setup(self, console=True, copyDongle=None):
rflib/chipcon_usb.py:623:    def getDebugCodes(self, timeout=100):
rflib/chipcon_usb.py:698:    def getPartNum(self):
rflib/chipcon_usb.py:763:    def getBuildInfo(self):
rflib/chipcon_usb.py:767:    def getCompilerInfo(self):
rflib/chipcon_usb.py:771:    def getDeviceSerialNumber(self):
rflib/chipcon_usb.py:775:    def getInterruptRegisters(self):
'''

    def test_api_nic(self):
        self.assertEqual(self.d.getRadioConfig(), 0)
        '''
rflib/chipcon_nic.py:114:    def setRfMode(self, rfmode, parms=b''):
rflib/chipcon_nic.py:122:    def setModeTX(self):
rflib/chipcon_nic.py:129:    def setModeRX(self):
rflib/chipcon_nic.py:136:    def setModeIDLE(self):
rflib/chipcon_nic.py:190:    def getRadioConfig(self):
rflib/chipcon_nic.py:195:    def setRadioConfig(self, bytedef = None):
rflib/chipcon_nic.py:218:    def setLedMode(self, ledmode):
rflib/chipcon_nic.py:225:    def getMARCSTATE(self, radiocfg=None):
rflib/chipcon_nic.py:233:    def setRFRegister(self, regaddr, value, suppress=False):
rflib/chipcon_nic.py:256:    def setRFbits(self, addr, bitnum, bitsz, val, suppress=False):
rflib/chipcon_nic.py:266:    def setEnableCCA(self, mode=3, absthresh=0, relthresh=1, magn=3, radiocfg=None):
rflib/chipcon_nic.py:294:    def setFreq(self, freq=902000000, mhz=24, radiocfg=None, applyConfig=True):        
rflib/chipcon_nic.py:326:    def getFreq(self, mhz=24, radiocfg=None):
rflib/chipcon_nic.py:336:    def getFreqEst(self, radiocfg=None):
rflib/chipcon_nic.py:357:    def setPower(self, power=None, radiocfg=None, invert=False):
rflib/chipcon_nic.py:382:    def setMaxPower(self, radiocfg=None, invert=False):
rflib/chipcon_nic.py:400:    def setMdmModulation(self, mod, radiocfg=None, invert=False):
rflib/chipcon_nic.py:423:    def getMdmModulation(self, radiocfg=None):
rflib/chipcon_nic.py:432:    def getMdmChanSpc(self, mhz=24, radiocfg=None):
rflib/chipcon_nic.py:443:    def setMdmChanSpc(self, chanspc=None, chanspc_m=None, chanspc_e=None, mhz=24, radiocfg=None):
rflib/chipcon_nic.py:509:    def getPktLEN(self):
rflib/chipcon_nic.py:515:    def setEnablePktCRC(self, enable=True, radiocfg=None):
rflib/chipcon_nic.py:526:    def getEnablePktCRC(self, radiocfg=None):
rflib/chipcon_nic.py:533:    def setEnablePktDataWhitening(self, enable=True, radiocfg=None):
rflib/chipcon_nic.py:543:    def getEnablePktDataWhitening(self, radiocfg=None):
rflib/chipcon_nic.py:550:    def setPktPQT(self, num=3, radiocfg=None):
rflib/chipcon_nic.py:562:    def getPktPQT(self, radiocfg=None):
rflib/chipcon_nic.py:569:    def setEnablePktAppendStatus(self, enable=True, radiocfg=None):
rflib/chipcon_nic.py:582:    def getEnablePktAppendStatus(self, radiocfg=None):
rflib/chipcon_nic.py:594:    def setEnableMdmManchester(self, enable=True, radiocfg=None):
rflib/chipcon_nic.py:603:    def getEnableMdmManchester(self, radiocfg=None):
rflib/chipcon_nic.py:612:    def setEnableMdmFEC(self, enable=True, radiocfg=None):
rflib/chipcon_nic.py:622:    def getEnableMdmFEC(self, radiocfg=None):
rflib/chipcon_nic.py:631:    def setEnableMdmDCFilter(self, enable=True, radiocfg=None):
rflib/chipcon_nic.py:641:    def getEnableMdmDCFilter(self, radiocfg=None):
rflib/chipcon_nic.py:650:    def setFsIF(self, freq_if, mhz=24, radiocfg=None):
rflib/chipcon_nic.py:670:    def getFsIF(self, mhz=24, radiocfg=None):
rflib/chipcon_nic.py:679:    def setFsOffset(self, if_off, mhz=24, radiocfg=None):
rflib/chipcon_nic.py:693:    def getFsOffset(self, mhz=24, radiocfg=None):
rflib/chipcon_nic.py:701:    def getChannel(self, radiocfg=None):
rflib/chipcon_nic.py:709:    def setChannel(self, channr, radiocfg=None):
rflib/chipcon_nic.py:717:    def setMdmChanBW(self, bw, mhz=24, radiocfg=None):
rflib/chipcon_nic.py:786:    def getMdmChanBW(self, mhz=24, radiocfg=None):
rflib/chipcon_nic.py:797:    def setMdmDRate(self, drate, mhz=24, radiocfg=None):
rflib/chipcon_nic.py:825:    def getMdmDRate(self, mhz=24, radiocfg=None):
rflib/chipcon_nic.py:841:    def setMdmDeviatn(self, deviatn, mhz=24, radiocfg=None):
rflib/chipcon_nic.py:866:    def getMdmDeviatn(self, mhz=24, radiocfg=None):
rflib/chipcon_nic.py:876:    def getMdmSyncWord(self, radiocfg=None):
rflib/chipcon_nic.py:883:    def setMdmSyncWord(self, word, radiocfg=None):
rflib/chipcon_nic.py:893:    def getMdmSyncMode(self, radiocfg=None):
rflib/chipcon_nic.py:900:    def setMdmSyncMode(self, syncmode=SYNCM_15_of_16, radiocfg=None):
rflib/chipcon_nic.py:909:    def getMdmNumPreamble(self, radiocfg=None):
rflib/chipcon_nic.py:921:    def setMdmNumPreamble(self, preamble=MFMCFG1_NUM_PREAMBLE_4, radiocfg=None):
rflib/chipcon_nic.py:933:    def getBSLimit(self, radiocfg=None):
rflib/chipcon_nic.py:943:    def setBSLimit(self, bslimit, radiocfg=None):
rflib/chipcon_nic.py:1013:    def getRSSI(self):
rflib/chipcon_nic.py:1017:    def getLQI(self):
rflib/chipcon_nic.py:1022:    def setAESmode(self, aesmode=AES_CRYPTO_DEFAULT):
rflib/chipcon_nic.py:1068:    def getAESmode(self):
rflib/chipcon_nic.py:1074:    def setAESiv(self, iv= b'\0'*16):
rflib/chipcon_nic.py:1082:    def setAESkey(self, key= b'\0'*16):
rflib/chipcon_nic.py:1088:    def setAmpMode(self, ampmode=0):
rflib/chipcon_nic.py:1093:    def getAmpMode(self):
rflib/chipcon_nic.py:1099:    def setPktAddr(self, addr):
rflib/chipcon_nic.py:1102:    def getPktAddr(self):
rflib/chipcon_nic.py:1105:    def setEnDeCoder(self, endec=None):
rflib/chipcon_nic.py:1578:    def setup24330MHz(self):
rflib/chipcon_nic.py:1619:    def setup900MHz(self):
rflib/chipcon_nic.py:1659:    def setup900MHzHopTrans(self):
rflib/chipcon_nic.py:1698:    def setup900MHzContTrans(self):
rflib/chipcon_nic.py:1740:    def setup_rfstudio_902PktTx(self):
rflib/chipcon_nic.py:1802:    def getChannels(self, channels=[]):
rflib/chipcon_nic.py:1805:    def setChannels(self, channels=[]):
rflib/chipcon_nic.py:1820:    def setMACperiod(self, dwell_ms, mhz=24):
rflib/chipcon_nic.py:1845:    def setMACdata(self, data):
rflib/chipcon_nic.py:1849:    def getMACdata(self):
rflib/chipcon_nic.py:1887:    def getMACthreshold(self):
rflib/chipcon_nic.py:1890:    def setMACthreshold(self, value):
rflib/chipcon_nic.py:1893:    def setFHSSstate(self, state):
rflib/chipcon_nic.py:1896:    def getFHSSstate(self):
rflib/chipcon_nic.py:2078:def getValueFromReprString(stringarray, line_text):
'''


    def test_bits(self):
        import rflib.bits as rfbits
        

    def test_intelhex(self):
        import rflib.intelhex as rfhex
        temphexfn = os.sep.join([tempfile.gettempdir(), 'rfcat_unittest_tempfile.hex'])
        # write the file first
        #open(temphexfn, 'w').write(testhex)
        with open(temphexfn, 'w') as f:
            f.write(testhex)

        ih = rfhex.IntelHex()
        ih.loadhex(temphexfn)



'''
rflib/bits.py:108:def getNextByte_feedbackRegister7bitsMSB():
rflib/bits.py:125:def getNextByte_feedbackRegister7bitsLSB():
rflib/bits.py:294:def getBit(data, bit):
rflib/__init__.py:184:    def setMdmSyncWord(self, word, radiocfg=None):

'''

'''  should figure out some unittest for these guys.
rfcat_msfrelay:70:    def set_freq(self, args):
rfcat_msfrelay:79:    def get_modulations(self):
rfcat_msfrelay:83:    def set_modulation(self, args):
rfcat_msfrelay:118:    def set_mode(self, args):
rfcat_msfrelay:140:    def set_channel(self, args):
rfcat_msfrelay:146:    def set_channel_bandwidth(self, args):
rfcat_msfrelay:155:    def set_channel_spc(self, args):
rfcat_msfrelay:172:    def set_baud_rate(self, args):
rfcat_msfrelay:184:    def set_deviation(self, args):
rfcat_msfrelay:196:    def set_sync_word(self, args):
rfcat_msfrelay:202:    def set_sync_mode(self, args):
rfcat_msfrelay:208:    def set_number_preamble(self, args):
rfcat_msfrelay:214:    def set_lowball(self):
rfcat_msfrelay:218:    def set_maxpower(self):
rfcat_msfrelay:222:    def set_power(self, args):
rfcat_server:815:    def getInterruptRegisters(self):
rfcat_server:819:    def getMACthreshold(self):
rfcat_server:820:    def setMACthreshold(self, value):
rfcat_server:821:    def setFHSSstate(self, state):
rfcat_server:822:    def getFHSSstate(self):
'''
