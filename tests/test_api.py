import os
import tempfile
import unittest
from rflib.const import *
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


d = FakeRfCat()

class TestApis(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        global d
        unittest.TestCase.__init__(self, *args, **kwargs)
        self.d = d

    def test_api_usb(self):
        self.assertEqual(self.d.getPartNum(), FAKE_PARTNUM)
        self.assertEqual(self.d.getDebugCodes(), FAKE_DEBUG_CODES)
        self.assertEqual(self.d.getBuildInfo(), FAKE_DONGLE_BUILDDATA)
        self.assertEqual(self.d.getCompilerInfo(), FAKE_DONGLE_COMPILER)
        self.assertEqual(self.d.getDeviceSerialNumber(), FAKE_DONGLE_SERIALNUM)
        self.assertEqual(self.d.getInterruptRegisters(), FAKE_INTERRUPT_REGISTERS)
        
        '''
        rflib/chipcon_usb.py:106:    def setRFparameters(self):
        '''

    def test_api_nic(self):
        self.assertEqual(self.d.getRadioConfig(), FAKE_MEM_DF00)
        #self.d.printRadioConfig()
        self.d.setRadioConfig(bytedef=b'@'*0x3a)
        self.assertEqual(self.d.getRadioConfig(), b'@'*0x3a + b'\xaa\r\x90\xfd')
        self.d.setRadioConfig(bytedef=FAKE_MEM_DF00)
        self.d.setModeRX()
        self.d.poke(X_RFST, b'%c'%RFST_SRX)
        self.assertEqual(self.d.getRadioConfig()[:-5], FAKE_MEM_DF00[:-5])
        self.d.printRadioConfig()

        self.d.setRfMode(RFST_SRX)
        self.assertEqual(ord(self.d.peek(X_RFST)), RFST_SRX)
        self.d.setModeTX()
        self.assertEqual(ord(self.d.peek(X_RFST)), RFST_STX)
        self.d.setModeRX()
        self.assertEqual(ord(self.d.peek(X_RFST)), RFST_SRX)
        self.d.setModeIDLE()
        self.assertEqual(ord(self.d.peek(X_RFST)), RFST_SIDLE)

        self.d.setLedMode(1)
        self.d.setLedMode(0)
        self.d.getMARCSTATE()

        self.d.setEnableCCA()
        
        self.d.setFreq(878e6)
        freq, freqnum = self.d.getFreq()
        self.assertAlmostEqual(freq, 878e6, delta=200)
        self.d.setPower(0xc0)
        self.d.setMaxPower()

        self.assertEqual(self.d.getPktLEN(), (255,0))
        self.d.setPktPQT(3)
        self.assertEqual(self.d.getPktPQT(), 3)
        self.d.setMdmModulation(MOD_4FSK)
        self.assertEqual(self.d.getMdmModulation(), MOD_4FSK)
        
        self.d.setMdmChanSpc(chanspc=333e3)
        self.assertAlmostEqual(self.d.getMdmChanSpc(), 333e3, delta=300)

        self.d.setEnablePktCRC()
        self.assertEqual(self.d.getEnablePktCRC(), True)

        self.d.setEnablePktDataWhitening()
        self.assertEqual(self.d.getEnablePktDataWhitening(), True)

        self.d.setEnablePktAppendStatus()
        self.assertEqual(self.d.getEnablePktAppendStatus(), True)

        self.d.setEnableMdmManchester()
        self.assertEqual(self.d.getEnableMdmManchester(), True)

        self.d.setEnableMdmFEC()
        self.assertEqual(self.d.getEnableMdmFEC(), True)

        self.d.setEnableMdmDCFilter()
        self.assertEqual(self.d.getEnableMdmDCFilter(), True)

        self.d.setFsIF(freq_if=23e3)
        self.d.getFsIF()

        self.d.setAmpMode(ampmode=1)
        self.d.getAmpMode()
        self.d.setPktAddr(addr=4)
        self.d.getPktAddr()

        '''
        setRFbits(self, addr, bitnum, bitsz, val, suppress=False):
        setFsOffset(self, if_off, mhz=24, radiocfg=None):
        getFsOffset(self, mhz=24, radiocfg=None):
        getChannel(self, radiocfg=None):
        setChannel(self, channr, radiocfg=None):
        setMdmChanBW(self, bw, mhz=24, radiocfg=None):
        getMdmChanBW(self, mhz=24, radiocfg=None):
        setMdmDRate(self, drate, mhz=24, radiocfg=None):
        getMdmDRate(self, mhz=24, radiocfg=None):
        setMdmDeviatn(self, deviatn, mhz=24, radiocfg=None):
        getMdmDeviatn(self, mhz=24, radiocfg=None):
        getMdmSyncWord(self, radiocfg=None):
        setMdmSyncWord(self, word, radiocfg=None):
        getMdmSyncMode(self, radiocfg=None):
        setMdmSyncMode(self, syncmode=SYNCM_15_of_16, radiocfg=None):
        getMdmNumPreamble(self, radiocfg=None):
        setMdmNumPreamble(self, preamble=MFMCFG1_NUM_PREAMBLE_4, radiocfg=None):
        getBSLimit(self, radiocfg=None):
        setBSLimit(self, bslimit, radiocfg=None):
        getRSSI(self):
        getLQI(self):
        setAESmode(self, aesmode=AES_CRYPTO_DEFAULT):
        getAESmode(self):
        setAESiv(self, iv= b'\0'*16):
        setAESkey(self, key= b'\0'*16):
        setEnDeCoder(self, endec=None):
        setup900MHz(self):
        setup900MHzHopTrans(self):
        setup900MHzContTrans(self):
        getChannels(self, channels=[]):
        setChannels(self, channels=[]):
        setMACperiod(self, dwell_ms, mhz=24):
        setMACdata(self, data):
        getMACdata(self):
        getMACthreshold(self):
        setMACthreshold(self, value):
        setFHSSstate(self, state):
        getFHSSstate(self):
        getValueFromReprString(stringarray, line_text):
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
